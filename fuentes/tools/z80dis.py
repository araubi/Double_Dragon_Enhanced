#!/usr/bin/env python3
"""Small Z80 disassembler (full documented + common undocumented set) with MSX symbol names.
usage: z80dis.py file.bin org [start end] [--entry addr ...]  (hex)
Does recursive traversal from entries to separate code/data, then linear dump."""
import sys

R = ['b','c','d','e','h','l','(hl)','a']
RP = ['bc','de','hl','sp']; RP2 = ['bc','de','hl','af']
CC = ['nz','z','nc','c','po','pe','p','m']
ALU = ['add a,','adc a,','sub ','sbc a,','and ','xor ','or ','cp ']
ROT = ['rlc','rrc','rl','rr','sla','sra','sll','srl']

BIOS = {0x0000:'CHKRAM',0x0008:'SYNCHR',0x000C:'RDSLT',0x0010:'CHRGTR',0x0014:'WRSLT',0x0018:'OUTDO',
0x001C:'CALSLT',0x0020:'DCOMPR',0x0024:'ENASLT',0x0028:'GETYPR',0x0030:'CALLF',0x0038:'KEYINT',
0x003B:'INITIO',0x003E:'INIFNK',0x0041:'DISSCR',0x0044:'ENASCR',0x0047:'WRTVDP',0x004A:'RDVRM',
0x004D:'WRTVRM',0x0050:'SETRD',0x0053:'SETWRT',0x0056:'FILVRM',0x0059:'LDIRMV',0x005C:'LDIRVM',
0x005F:'CHGMOD',0x0062:'CHGCLR',0x0066:'NMI',0x0069:'CLRSPR',0x006C:'INITXT',0x006F:'INIT32',
0x0072:'INIGRP',0x0075:'INIMLT',0x0078:'SETTXT',0x007B:'SETT32',0x007E:'SETGRP',0x0081:'SETMLT',
0x0084:'CALPAT',0x0087:'CALATR',0x008A:'GSPSIZ',0x008D:'GRPPRT',0x0090:'GICINI',0x0093:'WRTPSG',
0x0096:'RDPSG',0x0099:'STRTMS',0x009C:'CHSNS',0x009F:'CHGET',0x00A2:'CHPUT',0x00A5:'LPTOUT',
0x00A8:'LPTSTT',0x00AB:'CNVCHR',0x00AE:'PINLIN',0x00B1:'INLIN',0x00B4:'QINLIN',0x00B7:'BREAKX',
0x00BA:'ISCNTC',0x00BD:'CKCNTC',0x00C0:'BEEP',0x00C3:'CLS',0x00C6:'POSIT',0x00C9:'FNKSB',
0x00CC:'ERAFNK',0x00CF:'DSPFNK',0x00D2:'TOTEXT',0x00D5:'GTSTCK',0x00D8:'GTTRIG',0x00DB:'GTPAD',
0x00DE:'GTPDL',0x00E1:'TAPION',0x00E4:'TAPIN',0x00E7:'TAPIOF',0x00EA:'TAPOON',0x00ED:'TAPOUT',
0x00F0:'TAPOOF',0x00F3:'STMOTR',0x00F6:'LFTQ',0x00F9:'PUTQ',0x0132:'CHGCAP',0x0135:'CHGSND',
0x0138:'RSLREG',0x013B:'WSLREG',0x013E:'RDVDP',0x0141:'SNSMAT',0x0144:'PHYDIO',0x0156:'KILBUF',
0x015C:'SUBROM',0x015F:'EXTROM',0x0180:'CHGCPU',0x0183:'GETCPU',
0xF3DB:'CLIKSW',0xF3E9:'FORCLR',0xF3EA:'BAKCLR',0xF3EB:'BDRCLR',0xF3DF:'RG0SAV',0xF3E0:'RG1SAV',
0xF3E1:'RG2SAV',0xF3E2:'RG3SAV',0xF3E3:'RG4SAV',0xF3E4:'RG5SAV',0xF3E5:'RG6SAV',0xF3E6:'RG7SAV',
0xFCC1:'EXPTBL',0xFCC5:'SLTTBL',0xFD9A:'H.KEYI',0xFD9F:'H.TIMI',0xFC9E:'JIFFY',0xFCA9:'CSRSW',
0xF3AE:'LINL40',0xF3B0:'LINLEN',0xFBE5:'NEWKEY',0xFC48:'BOTTOM',0xFC4A:'HIMEM',0xF672:'MEMSIZ',
0xF674:'STKTOP',0xFFFF:'SLOTSEL',0xF380:'RDPRIM',0xFEDA:'H.STKE',0xFFE7:'RG8SAV',0x002D:'MSXVER',
0x0006:'VDP_DR',0x0007:'VDP_DW',0xFCAF:'SCRMOD',0xF3E8:'STATFL',0xFBEC:'TRGFLG'}
PORTS = {0x98:'VDP_DATA',0x99:'VDP_CTRL',0xA0:'PSG_ADDR',0xA1:'PSG_WR',0xA2:'PSG_RD',0xA8:'PPI_A',
0xA9:'PPI_B',0xAA:'PPI_C',0xAB:'PPI_CTRL',0x7C:'FM_ADDR',0x7D:'FM_DATA',0xFE:'MAP_P2',0xFF:'MAP_P3'}

class Dis:
    def __init__(s, data, org):
        s.d = data; s.org = org
    def b(s, a):
        i = a - s.org
        return s.d[i] if 0 <= i < len(s.d) else 0
    def w(s, a): return s.b(a) | (s.b(a+1) << 8)
    def sym(s, v, word=True):
        if v in BIOS and word: return BIOS[v]
        return ('%04Xh' if word else '%02Xh') % v if True else ''
    def hexn(s, v): return ('0%Xh' if f'{v:X}'[0] in 'ABCDEF' else '%Xh') % v
    def addr(s, v):
        n = BIOS.get(v)
        return n if n else ('L%04X' % v)

    def dec(s, pc):
        """returns (text, length, flow, targets) flow in {None,'jp','jr','call','ret','stop'}"""
        p0 = pc; op = s.b(pc); pc += 1
        idx = None; disp = None
        if op in (0xDD, 0xFD):
            idx = 'ix' if op == 0xDD else 'iy'
            op = s.b(pc); pc += 1
            if op in (0xDD, 0xFD, 0xED):
                return ('db %s' % s.hexn(s.b(p0)), 1, None, [])
        def rr(i):  # register with index substitution
            nonlocal pc, disp
            if idx is None: return R[i]
            if i == 6:
                if disp is None:
                    disp = s.b(pc); pc += 1
                dd = disp - 256 if disp > 127 else disp
                return '(%s%+d)' % (idx, dd)
            return R[i]
        def rrh(i):  # for undocumented ixh/ixl when no (hl) in instr
            if idx is None: return R[i]
            if i == 4: return idx + 'h'
            if i == 5: return idx + 'l'
            return R[i]
        def hl(): return idx or 'hl'
        def rp(i): return hl() if i == 2 else RP[i]
        def rp2(i): return hl() if i == 2 else RP2[i]
        def n8():
            nonlocal pc
            v = s.b(pc); pc += 1; return v
        def n16():
            nonlocal pc
            v = s.w(pc); pc += 2; return v
        if op == 0xCB:
            if idx:
                disp = s.b(pc); pc += 1; op2 = s.b(pc); pc += 1
                dd = disp - 256 if disp > 127 else disp
                m = '(%s%+d)' % (idx, dd)
            else:
                op2 = s.b(pc); pc += 1; m = None
            x, y, z = op2 >> 6, (op2 >> 3) & 7, op2 & 7
            tgt = m if m else R[z]
            if x == 0: t = '%s %s' % (ROT[y], tgt)
            else: t = '%s %d,%s' % (['', 'bit', 'res', 'set'][x], y, tgt)
            return (t, pc - p0, None, [])
        if op == 0xED and idx is None:
            op2 = s.b(pc); pc += 1
            x, y, z = op2 >> 6, (op2 >> 3) & 7, op2 & 7; p, q = y >> 1, y & 1
            t = None; flow = None
            if x == 1:
                if z == 0: t = 'in %s,(c)' % R[y] if y != 6 else 'in f,(c)'
                elif z == 1: t = 'out (c),%s' % R[y] if y != 6 else 'out (c),0'
                elif z == 2: t = ('sbc hl,%s' if q == 0 else 'adc hl,%s') % RP[p]
                elif z == 3:
                    v = n16()
                    t = ('ld (%s),%s' % (s.sym(v), RP[p])) if q == 0 else ('ld %s,(%s)' % (RP[p], s.sym(v)))
                elif z == 4: t = 'neg'
                elif z == 5: t = 'reti' if y == 1 else 'retn'; flow = 'ret'
                elif z == 6: t = 'im %s' % ['0', '0', '1', '2', '0', '0', '1', '2'][y]
                elif z == 7: t = ['ld i,a', 'ld r,a', 'ld a,i', 'ld a,r', 'rrd', 'rld', 'nop', 'nop'][y]
            elif x == 2 and z <= 3 and y >= 4:
                t = [['ldi', 'cpi', 'ini', 'outi'], ['ldd', 'cpd', 'ind', 'outd'],
                     ['ldir', 'cpir', 'inir', 'otir'], ['lddr', 'cpdr', 'indr', 'otdr']][y - 4][z]
            if t is None: t = 'db 0EDh,%s' % s.hexn(op2)
            return (t, pc - p0, flow, [])
        x, y, z = op >> 6, (op >> 3) & 7, op & 7; p, q = y >> 1, y & 1
        flow = None; tg = []
        if x == 0:
            if z == 0:
                if y == 0: t = 'nop'
                elif y == 1: t = "ex af,af'"
                else:
                    e = n8(); e = e - 256 if e > 127 else e; dst = (pc + e) & 0xFFFF
                    t = ['djnz', 'jr', 'jr nz,', 'jr z,', 'jr nc,', 'jr c,'][y - 2]
                    t = (t + ' ' if y < 4 else t) + s.addr(dst)
                    flow = 'jp' if y == 3 else 'jr'; tg = [dst]
            elif z == 1:
                if q == 0:
                    v = n16(); t = 'ld %s,%s' % (rp(p), s.sym(v))
                else: t = 'add %s,%s' % (hl(), rp(p))
            elif z == 2:
                if p < 2:
                    t = ['ld (bc),a', 'ld a,(bc)', 'ld (de),a', 'ld a,(de)'][p * 2 + q]
                else:
                    v = n16(); a = s.sym(v)
                    if p == 2: t = ('ld (%s),%s' % (a, hl())) if q == 0 else ('ld %s,(%s)' % (hl(), a))
                    else: t = ('ld (%s),a' % a) if q == 0 else ('ld a,(%s)' % a)
            elif z == 3: t = ('inc %s' if q == 0 else 'dec %s') % rp(p)
            elif z in (4, 5):
                t = ('inc %s' if z == 4 else 'dec %s') % (rr(y) if y == 6 else rrh(y))
            elif z == 6:
                r = rr(y) if y == 6 else rrh(y); v = n8(); t = 'ld %s,%s' % (r, s.hexn(v))
            else: t = ['rlca', 'rrca', 'rla', 'rra', 'daa', 'cpl', 'scf', 'ccf'][y]
        elif x == 1:
            if op == 0x76: t = 'halt'
            else:
                if y == 6 or z == 6: t = 'ld %s,%s' % (rr(y), rr(z))
                else: t = 'ld %s,%s' % (rrh(y), rrh(z))
        elif x == 2:
            t = ALU[y] + (rr(z) if z == 6 else rrh(z))
        else:
            if z == 0: t = 'ret ' + CC[y]; flow = None
            elif z == 1:
                if q == 0: t = 'pop ' + rp2(p)
                else:
                    t = ['ret', 'exx', 'jp (%s)' % hl(), 'ld sp,%s' % hl()][p]
                    if p == 0: flow = 'ret'
                    if p == 2: flow = 'stop'
            elif z == 2:
                v = n16(); t = 'jp %s,%s' % (CC[y], s.addr(v)); flow = 'jr'; tg = [v]
            elif z == 3:
                if y == 0: v = n16(); t = 'jp ' + s.addr(v); flow = 'jp'; tg = [v]
                elif y == 1: return ('?', 1, None, [])
                elif y == 2: v = n8(); t = 'out (%s),a' % PORTS.get(v, s.hexn(v))
                elif y == 3: v = n8(); t = 'in a,(%s)' % PORTS.get(v, s.hexn(v))
                else: t = ['ex (sp),%s' % hl(), 'ex de,hl', 'di', 'ei'][y - 4]
            elif z == 4: v = n16(); t = 'call %s,%s' % (CC[y], s.addr(v)); flow = 'call'; tg = [v]
            elif z == 5:
                if q == 0: t = 'push ' + rp2(p)
                elif p == 0: v = n16(); t = 'call ' + s.addr(v); flow = 'call'; tg = [v]
            elif z == 6: v = n8(); t = ALU[y] + s.hexn(v)
            else: t = 'rst %s' % s.hexn(y * 8); flow = 'call'; tg = []
        return (t, pc - p0, flow, tg)

def main():
    a = sys.argv[1:]
    entries = []
    if '--entry' in a:
        i = a.index('--entry'); entries = [int(x, 16) for x in a[i + 1:]]; a = a[:i]
    data = open(a[0], 'rb').read(); org = int(a[1], 16)
    st = int(a[2], 16) if len(a) > 2 else org
    en = int(a[3], 16) if len(a) > 3 else org + len(data)
    D = Dis(data, org)
    code = set(); labels = set(entries); work = list(entries)
    inr = lambda x: org <= x < org + len(data)
    seen = set()
    while work:
        pc = work.pop()
        while inr(pc) and pc not in seen:
            seen.add(pc)
            t, l, f, tg = D.dec(pc)
            for k in range(l): code.add(pc + k)
            for x in tg:
                labels.add(x)
                if inr(x) and x not in seen: work.append(x)
            if f in ('jp', 'ret', 'stop'): break
            pc += l
    pc = st
    out = []
    if not entries: code = set(range(st, en))
    while pc < en:
        if pc in labels: out.append('L%04X:' % pc)
        if pc in code:
            t, l, f, tg = D.dec(pc)
            hx = ' '.join('%02X' % D.b(pc + k) for k in range(l))
            out.append('  %04X  %-12s  %s' % (pc, hx, t))
            pc += l
        else:
            q = pc; bs = []
            while q < en and q not in code and len(bs) < 16 and (q == pc or q not in labels):
                bs.append(D.b(q)); q += 1
            asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in bs)
            out.append('  %04X  db %-48s ; %s' % (pc, ','.join('%02X' % c for c in bs), asc))
            pc = q
        if out[-1].split()[-1] in ('ret', 'reti', 'retn') or ' jp ' in out[-1] and ',' not in out[-1].split('jp')[-1]:
            out.append('')
    print('\n'.join(out))

if __name__ == '__main__': main()
