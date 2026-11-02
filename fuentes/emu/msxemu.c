// Minimal MSX1 test harness: Z80 (superzazu core) + slots/subslots + RAM/ROM/ASCII8 MegaROM
// + TMS9918 (ports, regs, VRAM, status, frame IRQ, access-interval checker, renderer)
// + PSG (regs, port A joystick, direction semantics like openMSX) + PPI keyboard.
// Driven from Python via ctypes.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "z80.h"

enum { DEV_NONE = 0, DEV_RAM, DEV_ROM, DEV_ASCII8 };
typedef struct { int type; uint8_t *data; uint32_t size; int base_page; uint8_t bank[4]; } Dev;

static z80 Z;
static Dev slots[4][4];           // [primary][secondary]
static int expanded[4];
static uint8_t subreg[4];
static uint8_t ppiA, ppiC;
static uint8_t keymatrix[11];     // bit=0 pressed
static uint8_t joyA = 0x3F;       // PSG port A pins: bit0 up,1 down,2 left,3 right,4 trigA,5 trigB (0 = active)

// VDP
static uint8_t vram[16384], vreg[8], vstat, vlatch, vlatch_on, vbuf;
static uint16_t vaddr;
static int vint_line;
static unsigned long frame_start, next_vb = 192*228;
#define LINE_T 228
#define LINES 262
#define FRAME_T (LINE_T*LINES)
static unsigned long last_vacc;
static int vacc_valid;
unsigned long vdp_viol_active, vdp_viol_vblank, vdp_accesses, vdp_min_active_gap = 999;
static uint16_t viol_pc_hist_pc[64]; static unsigned long viol_pc_hist_n[64]; static int viol_pc_cnt;

// PSG
static uint8_t psg_sel, psg[16];

// stats / hooks
static uint8_t exec_map[65536];
static uint32_t ix_exec[65536]; static uint16_t ix_lo=1, ix_hi=0;   // address-level (whatever is mapped)
static uint8_t watch_map[65536];
static uint8_t read_map[65536];
static uint8_t rwatch_map[65536];
unsigned long rwatch_hist[65536];
static uint8_t write_map[65536];
static uint8_t wexcl_map[65536];
void emu_wexcl(int lo, int hi, int on) { for (int i = lo; i <= hi; i++) wexcl_map[i] = on; }
unsigned long watch_hist[65536];
uint16_t wlog_pc[200000], wlog_a[200000]; int wlog_n;
int emu_wlog(uint16_t **pc, uint16_t **a) { *pc = wlog_pc; *a = wlog_a; int n = wlog_n; wlog_n = 0; return n; }
static uint16_t cur_pc;
unsigned long vregw_hist[65536], vramw_hist[65536], vaddrw_hist[65536];
unsigned long *emu_vregw_hist(void){return vregw_hist;}
unsigned long *emu_vramw_hist(void){return vramw_hist;}
unsigned long *emu_vaddrw_hist(void){return vaddrw_hist;}
void emu_vw_clear(void){memset(vregw_hist,0,sizeof vregw_hist);memset(vramw_hist,0,sizeof vramw_hist);memset(vaddrw_hist,0,sizeof vaddrw_hist);}
static int det_r = 0; static uint32_t det_seed = 12345; static uint32_t det_cnt[65536];
static uint8_t bp_map[65536];
unsigned long frames;
static int stop_flag;
int last_stop_reason;

static Dev *devfor(uint16_t a, int *page_out) {
  int page = a >> 14; int p = (ppiA >> (page * 2)) & 3; int s = 0;
  if (expanded[p]) s = (subreg[p] >> (page * 2)) & 3;
  *page_out = page; return &slots[p][s];
}

static uint8_t rd(void *u, uint16_t a) {
  (void)u;
  int page; int p3 = (ppiA >> 6) & 3;
  if (a == 0xFFFF && expanded[p3]) return (uint8_t)~subreg[p3];
  read_map[a] = 1;
  if (rwatch_map[a] && a != Z.pc) rwatch_hist[cur_pc]++;
  Dev *d = devfor(a, &page);
  switch (d->type) {
    case DEV_RAM: return d->data[a];
    case DEV_ROM: { long off = (long)a - d->base_page * 16384; if (off >= 0 && off < (long)d->size) return d->data[off]; return 0xFF; }
    case DEV_ASCII8: { if (a < 0x4000 || a >= 0xC000) return 0xFF; int b = (a - 0x4000) >> 13; uint32_t off = ((uint32_t)d->bank[b] * 8192 + (a & 0x1FFF)) % d->size; return d->data[off]; }
  }
  return 0xFF;
}
static void wr(void *u, uint16_t a, uint8_t v) {
  (void)u;
  int page; int p3 = (ppiA >> 6) & 3;
  if (a == 0xFFFF && expanded[p3]) { subreg[p3] = v; return; }
  if (watch_map[a]) { watch_hist[cur_pc]++; if (wlog_n < 200000) { wlog_pc[wlog_n] = cur_pc; wlog_a[wlog_n++] = a; } }
  if (!wexcl_map[cur_pc]) write_map[a] = 1;
  Dev *d = devfor(a, &page);
  if (d->type == DEV_RAM) d->data[a] = v;
  else if (d->type == DEV_ASCII8) { if (a >= 0x6000 && a < 0x8000) d->bank[(a - 0x6000) >> 11] = v; }
}

static void vdp_access(void) {
  unsigned long now = Z.cyc;
  vdp_accesses++;
  if (vacc_valid) {
    unsigned long gap = now - last_vacc;
    unsigned long pos = (now - frame_start) % FRAME_T; int line = pos / LINE_T;
    int disp_on = vreg[1] & 0x40;
    if (line < 192 && disp_on) {
      if (gap < vdp_min_active_gap) vdp_min_active_gap = gap;
      if (gap < 29) { vdp_viol_active++;
        int i; for (i = 0; i < viol_pc_cnt; i++) if (viol_pc_hist_pc[i] == cur_pc) break;
        if (i == viol_pc_cnt && viol_pc_cnt < 64) { viol_pc_hist_pc[viol_pc_cnt] = cur_pc; viol_pc_hist_n[viol_pc_cnt++] = 0; }
        if (i < 64) viol_pc_hist_n[i]++; }
    } else if (gap < 12) vdp_viol_vblank++;
  }
  last_vacc = now; vacc_valid = 1;
}

static uint8_t pin(z80 *z, uint8_t port) {
  (void)z;
  switch (port) {
    case 0x98: { vdp_access(); uint8_t r = vbuf; vbuf = vram[vaddr]; vaddr = (vaddr + 1) & 0x3FFF; vlatch_on = 0; return r; }
    case 0x99: { uint8_t r = vstat; vstat &= 0x1F; vint_line = 0; vlatch_on = 0; return r; }
    case 0xA2: {
      if (psg_sel == 14) { if (!(psg[7] & 0x40)) { // input mode
          uint8_t v = (psg[15] & 0x40) ? 0x3F : joyA; psg[14] = v | 0xC0; }
        return psg[14]; }
      return psg[psg_sel & 15]; }
    case 0xA8: return ppiA;
    case 0xA9: { int row = ppiC & 15; return row < 11 ? keymatrix[row] : 0xFF; }
    case 0xAA: return ppiC;
  }
  return 0xFF;
}
static void pout(z80 *z, uint8_t port, uint8_t v) {
  (void)z;
  switch (port) {
    case 0x98: vramw_hist[cur_pc]++; vdp_access(); vram[vaddr] = v; vbuf = v; vaddr = (vaddr + 1) & 0x3FFF; vlatch_on = 0; break;
    case 0x99:
      if (!vlatch_on) { vlatch = v; vlatch_on = 1; }
      else { vlatch_on = 0;
        if (v & 0x80) { vregw_hist[cur_pc]++; vreg[v & 7] = vlatch; if ((v & 7) == 1 && (vlatch & 0x20) && (vstat & 0x80)) vint_line = 1; if ((v&7)==1 && !(vlatch&0x20)) vint_line=0; }
        else { vaddrw_hist[cur_pc]++; vaddr = ((v & 0x3F) << 8) | vlatch; if (!(v & 0x40)) { vbuf = vram[vaddr]; vaddr = (vaddr + 1) & 0x3FFF; } } }
      break;
    case 0xA0: psg_sel = v & 15; break;
    case 0xA1: psg[psg_sel] = v; break;
    case 0xA8: ppiA = v; break;
    case 0xAA: ppiC = v; break;
    case 0xAB: if (!(v & 0x80)) { int bit = (v >> 1) & 7; if (v & 1) ppiC |= 1 << bit; else ppiC &= ~(1 << bit); } break;
  }
}

// ---------- API ----------
int emu_init(void) {
  memset(slots, 0, sizeof slots); memset(expanded, 0, sizeof expanded); memset(subreg, 0, sizeof subreg);
  memset(keymatrix, 0xFF, sizeof keymatrix); memset(vram, 0, sizeof vram); memset(vreg, 0, sizeof vreg);
  memset(psg, 0, sizeof psg); psg[7] = 0xBF; psg[14] = 0xFF;
  memset(exec_map, 0, sizeof exec_map); memset(watch_map, 0, sizeof watch_map); memset(watch_hist, 0, sizeof watch_hist);
  memset(bp_map, 0, sizeof bp_map);
  vstat = 0; vlatch_on = 0; vaddr = 0; vint_line = 0; ppiA = 0; ppiC = 0; frames = 0;
  vdp_viol_active = vdp_viol_vblank = vdp_accesses = 0; vdp_min_active_gap = 999; vacc_valid = 0; viol_pc_cnt = 0;
  z80_init(&Z);
  Z.read_byte = rd; Z.write_byte = wr; Z.port_in = pin; Z.port_out = pout;
  Z.cyc = 0; frame_start = 0; next_vb = 192 * LINE_T;
  return 0;
}
void emu_set_expanded(int p, int e) { expanded[p] = e; }
uint8_t *emu_add_ram(int p, int s) { Dev *d = &slots[p][s]; d->type = DEV_RAM; d->data = calloc(65536, 1); memset(d->data, 0xFF, 65536); d->size = 65536; return d->data; }
void emu_add_rom(int p, int s, const uint8_t *data, uint32_t size, int base_page) { Dev *d = &slots[p][s]; d->type = DEV_ROM; d->data = malloc(size); memcpy(d->data, data, size); d->size = size; d->base_page = base_page; }
void emu_add_ascii8(int p, int s, const uint8_t *data, uint32_t size) { Dev *d = &slots[p][s]; d->type = DEV_ASCII8; d->data = malloc(size); memcpy(d->data, data, size); d->size = size; memset(d->bank, 0, 4); }
uint8_t *emu_ram_ptr(int p, int s) { return slots[p][s].type == DEV_RAM ? slots[p][s].data : NULL; }
void emu_set_slots(uint8_t a8, uint8_t sub0, uint8_t sub1, uint8_t sub2, uint8_t sub3) { ppiA = a8; subreg[0] = sub0; subreg[1] = sub1; subreg[2] = sub2; subreg[3] = sub3; }
uint8_t emu_get_ppiA(void) { return ppiA; }
uint8_t emu_get_sub(int p) { return subreg[p]; }
uint8_t emu_peek(uint16_t a) { return rd(0, a); }
void emu_poke(uint16_t a, uint8_t v) { uint8_t w = watch_map[a]; watch_map[a] = 0; wr(0, a, v); watch_map[a] = w; }
uint8_t *emu_vram(void) { return vram; }
uint8_t *emu_vregs(void) { return vreg; }
void emu_set_vreg(int r, uint8_t v) { vreg[r & 7] = v; }
uint8_t *emu_psg(void) { return psg; }
uint8_t *emu_exec_map(void) { return exec_map; }
uint32_t *emu_ix_exec(void) { return ix_exec; }
void emu_ix_filter(int lo, int hi) { ix_lo = lo; ix_hi = hi; memset(ix_exec, 0, sizeof ix_exec); }
uint8_t *emu_read_map(void) { return read_map; }
uint8_t *emu_rwatch_map(void) { return rwatch_map; }
unsigned long *emu_rwatch_hist(void) { return rwatch_hist; }
uint8_t *emu_write_map(void) { return write_map; }
void emu_clear_maps(void) { memset(exec_map,0,65536); memset(read_map,0,65536); memset(write_map,0,65536); }
uint8_t *emu_watch_map(void) { return watch_map; }
unsigned long *emu_watch_hist(void) { return watch_hist; }
uint8_t *emu_bp_map(void) { return bp_map; }
void emu_set_key(int row, int bit, int pressed) { if (pressed) keymatrix[row] &= ~(1 << bit); else keymatrix[row] |= 1 << bit; }
void emu_set_joy(uint8_t v) { joyA = v; }
void emu_set_det_r(int on, uint32_t seed) { det_r = on; det_seed = seed; memset(det_cnt, 0, sizeof det_cnt); }
unsigned long emu_cycles(void) { return Z.cyc; }
unsigned long emu_frames(void) { return frames; }

// registers access: idx 0 pc 1 sp 2 af 3 bc 4 de 5 hl 6 ix 7 iy
static uint8_t getf(void) { return (Z.sf << 7) | (Z.zf << 6) | (Z.yf << 5) | (Z.hf << 4) | (Z.xf << 3) | (Z.pf << 2) | (Z.nf << 1) | Z.cf; }
static void setf(uint8_t f) { Z.sf = f >> 7 & 1; Z.zf = f >> 6 & 1; Z.yf = f >> 5 & 1; Z.hf = f >> 4 & 1; Z.xf = f >> 3 & 1; Z.pf = f >> 2 & 1; Z.nf = f >> 1 & 1; Z.cf = f & 1; }
int emu_get_reg(int i) {
  switch (i) { case 0: return Z.pc; case 1: return Z.sp; case 2: return Z.a << 8 | getf(); case 3: return Z.b << 8 | Z.c;
    case 4: return Z.d << 8 | Z.e; case 5: return Z.h << 8 | Z.l; case 6: return Z.ix; case 7: return Z.iy; case 8: return Z.iff1; case 9: return Z.interrupt_mode; case 10: return Z.i; }
  return 0; }
void emu_set_reg(int i, int v) {
  switch (i) { case 0: Z.pc = v; break; case 1: Z.sp = v; break; case 2: Z.a = v >> 8; setf(v & 255); break; case 3: Z.b = v >> 8; Z.c = v; break;
    case 4: Z.d = v >> 8; Z.e = v; break; case 5: Z.h = v >> 8; Z.l = v; break; case 6: Z.ix = v; break; case 7: Z.iy = v; break; case 8: Z.iff1 = Z.iff2 = v; break; } }

// one step with MSX M1 wait states; returns 1 if a frame boundary passed
static void step(void) {
  uint16_t pc = Z.pc; cur_pc = pc;
  exec_map[pc] = 1;
  if (Z.ix >= ix_lo && Z.ix <= ix_hi) ix_exec[pc]++;
  uint8_t op = rd(0, pc), op2 = rd(0, pc + 1);
  int m1 = 1; if (op == 0xCB || op == 0xED || op == 0xDD || op == 0xFD) m1 = 2;
  int is_ldar = (op == 0xED && op2 == 0x5F);
  if (vint_line && Z.iff1) z80_gen_int(&Z, 0xFF); else Z.int_pending = 0;
  unsigned long c0 = Z.cyc;
  z80_step(&Z);
  if (Z.cyc != c0) Z.cyc += m1;  // M1 wait state(s)
  if (is_ldar && det_r) { uint32_t x = det_seed ^ (pc * 2654435761u) ^ (det_cnt[pc]++ * 40503u); x ^= x >> 15; x *= 2246822519u; x ^= x >> 13; x *= 3266489917u; x ^= x >> 16; uint8_t v = x & 0xFF; Z.a = v; Z.sf = v >> 7; Z.zf = v == 0; Z.hf = 0; Z.nf = 0; Z.pf = Z.iff2; }
  while (Z.cyc >= next_vb) { // entering vblank
    vstat |= 0x80; if (vreg[1] & 0x20) vint_line = 1;
    frame_start = next_vb - 192 * LINE_T; next_vb += FRAME_T; frames++;
  }
}

// run until breakpoint hit (checked BEFORE executing that pc), or max cycles elapsed. returns 1=bp, 0=timeout
int emu_run(unsigned long max_cycles) {
  unsigned long end = Z.cyc + max_cycles; int first = 1;
  while (Z.cyc < end) {
    if (!first && bp_map[Z.pc]) { last_stop_reason = 1; return 1; }
    first = 0; step();
  }
  last_stop_reason = 0; return 0;
}
int emu_step1(void) { step(); return Z.pc; }
unsigned long emu_viol(int which) { return which == 0 ? vdp_viol_active : which == 1 ? vdp_viol_vblank : which == 2 ? vdp_accesses : vdp_min_active_gap; }
void emu_viol_reset(void) { vdp_viol_active = vdp_viol_vblank = vdp_accesses = 0; vdp_min_active_gap = 999; viol_pc_cnt = 0; vacc_valid = 0; }
int emu_viol_list(uint16_t *pcs, unsigned long *ns) { for (int i = 0; i < viol_pc_cnt; i++) { pcs[i] = viol_pc_hist_pc[i]; ns[i] = viol_pc_hist_n[i]; } return viol_pc_cnt; }

// ---------- renderer (no sprites except basic) ----------
static const uint8_t pal[16][3] = {{0,0,0},{0,0,0},{33,200,66},{94,220,120},{84,85,237},{125,118,252},{212,82,77},{66,235,245},
  {252,85,84},{255,121,120},{212,193,84},{230,206,128},{33,176,59},{201,91,186},{204,204,204},{255,255,255}};
void emu_render(uint8_t *rgb) { // 256x192 RGB
  int m1 = (vreg[1] >> 4) & 1, m2 = (vreg[1] >> 3) & 1, m3 = (vreg[0] >> 1) & 1;
  uint8_t bd = vreg[7] & 15;
  for (int y = 0; y < 192; y++) for (int x = 0; x < 256; x++) {
    int c = bd;
    if (vreg[1] & 0x40) {
      if (m3 && !m1 && !m2) { // Graphic II
        int nt = (vreg[2] & 0xF) * 0x400, row = y >> 3, col = x >> 3, third = row >> 3;
        int ch = vram[nt + row * 32 + col] + third * 256;
        int pg = ((vreg[4] & 4) ? 0x2000 : 0) + ((ch & (((vreg[4] & 3) << 8) | 0xFF)) << 3) + (y & 7);
        int ct = ((vreg[3] & 0x80) ? 0x2000 : 0) + ((ch & (((vreg[3] & 0x7F) << 3) | 7)) << 3) + (y & 7);
        int bit = (vram[pg & 0x3FFF] >> (7 - (x & 7))) & 1; int col8 = vram[ct & 0x3FFF];
        c = bit ? col8 >> 4 : col8 & 15;
      } else if (!m1 && !m2 && !m3) { // Graphic I
        int nt = (vreg[2] & 0xF) * 0x400, ch = vram[nt + (y >> 3) * 32 + (x >> 3)];
        int bit = (vram[(vreg[4] & 7) * 0x800 + ch * 8 + (y & 7)] >> (7 - (x & 7))) & 1;
        int col8 = vram[vreg[3] * 0x40 + (ch >> 3)]; c = bit ? col8 >> 4 : col8 & 15;
      } else if (m1) { // text 40x24, 6px chars, 8px margins
        if (x >= 8 && x < 248) { int cx = (x - 8) / 6, px = (x - 8) % 6; int nt = (vreg[2] & 0xF) * 0x400; int ch = vram[nt + (y >> 3) * 40 + cx];
          int bit = (vram[(vreg[4] & 7) * 0x800 + ch * 8 + (y & 7)] >> (7 - px)) & 1; c = bit ? vreg[7] >> 4 : vreg[7] & 15; }
      }
      if (c == 0) c = bd;
    }
    uint8_t *o = rgb + (y * 256 + x) * 3; o[0] = pal[c][0]; o[1] = pal[c][1]; o[2] = pal[c][2];
  }
}
