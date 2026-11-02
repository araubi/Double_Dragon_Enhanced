"""Python driver for libmsx.so (MSX1 test harness)."""
import ctypes as C, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
import shutil
_LIBS = {}


def _lib(idx):
    if idx in _LIBS:
        return _LIBS[idx]
    src = os.path.join(HERE, 'libmsx.so')
    path = src if idx == 0 else os.path.join(HERE, 'libmsx_%d.so' % idx)
    if idx:
        shutil.copyfile(src, path)
    L = C.CDLL(path)
    L.emu_add_ram.restype = C.POINTER(C.c_uint8)
    L.emu_ram_ptr.restype = C.POINTER(C.c_uint8)
    L.emu_vram.restype = C.POINTER(C.c_uint8)
    L.emu_vregs.restype = C.POINTER(C.c_uint8)
    L.emu_psg.restype = C.POINTER(C.c_uint8)
    L.emu_exec_map.restype = C.POINTER(C.c_uint8)
    L.emu_ix_exec.restype = C.POINTER(C.c_uint32)
    L.emu_read_map.restype = C.POINTER(C.c_uint8)
    L.emu_write_map.restype = C.POINTER(C.c_uint8)
    L.emu_rwatch_map.restype = C.POINTER(C.c_uint8)
    L.emu_rwatch_hist.restype = C.POINTER(C.c_ulong)
    L.emu_watch_map.restype = C.POINTER(C.c_uint8)
    L.emu_watch_hist.restype = C.POINTER(C.c_ulong)
    L.emu_bp_map.restype = C.POINTER(C.c_uint8)
    L.emu_cycles.restype = C.c_ulong
    L.emu_frames.restype = C.c_ulong
    L.emu_viol.restype = C.c_ulong
    L.emu_run.argtypes = [C.c_ulong]
    L.emu_peek.restype = C.c_uint8
    _LIBS[idx] = L
    return L


KEYS = {'SPACE': (8, 0), 'LEFT': (8, 4), 'UP': (8, 5), 'DOWN': (8, 6), 'RIGHT': (8, 7), 'RET': (7, 7),
        'SHIFT': (6, 0), 'W': (5, 4), 'S': (5, 0), 'D': (3, 1), 'O': (4, 4), 'P': (4, 5), 'Q': (4, 6), 'A': (2, 6), 'M': (4, 2), 'Z': (5, 7), 'ESC': (7, 2)}


_next_instance = [0]


class MSX:
    def __init__(self, instance=None):
        if instance is None:
            instance = _next_instance[0]; _next_instance[0] += 1
        self.L = _lib(instance)
        self.L.emu_init()

    # memory
    def ram(self, p=3, s=0):
        ptr = self.L.emu_ram_ptr(p, s)
        return C.cast(ptr, C.POINTER(C.c_uint8 * 65536)).contents

    def add_ram(self, p, s=0):
        self.L.emu_add_ram(p, s)
        return self.ram(p, s)

    def add_rom(self, p, s, data, base_page):
        self.L.emu_add_rom(p, s, data, len(data), base_page)

    def add_ascii8(self, p, s, data):
        self.L.emu_add_ascii8(p, s, data, len(data))

    def expanded(self, p, e=1):
        self.L.emu_set_expanded(p, e)

    def slots(self, a8, subs=(0, 0, 0, 0)):
        self.L.emu_set_slots(a8, *subs)

    def peek(self, a):
        return self.L.emu_peek(a)

    def poke(self, a, v):
        self.L.emu_poke(a, v)

    def peekw(self, a):
        return self.peek(a) | self.peek(a + 1) << 8

    @property
    def vram(self):
        return C.cast(self.L.emu_vram(), C.POINTER(C.c_uint8 * 16384)).contents

    def vregs(self):
        r = self.L.emu_vregs()
        return [r[i] for i in range(8)]

    def set_vreg(self, r, v):
        self.L.emu_set_vreg(r, v)

    # cpu
    REG = {'pc': 0, 'sp': 1, 'af': 2, 'bc': 3, 'de': 4, 'hl': 5, 'ix': 6, 'iy': 7, 'iff': 8, 'im': 9, 'i': 10}

    def get(self, r):
        return self.L.emu_get_reg(self.REG[r])

    def set(self, r, v):
        self.L.emu_set_reg(self.REG[r], v)

    @property
    def cyc(self):
        return self.L.emu_cycles()

    @property
    def frames(self):
        return self.L.emu_frames()

    def bp(self, addrs, on=1):
        m = self.L.emu_bp_map()
        for a in addrs:
            m[a] = on

    def run(self, cycles):
        return self.L.emu_run(cycles)

    def run_until(self, addrs, max_cycles=50_000_000):
        self.bp(addrs, 1)
        r = self.L.emu_run(max_cycles)
        self.bp(addrs, 0)
        return r == 1

    def ret(self):  # emulate RET
        sp = self.get('sp')
        self.set('pc', self.peekw(sp))
        self.set('sp', sp + 2)

    # io
    def key(self, name, down=True):
        r, b = KEYS[name]
        self.L.emu_set_key(r, b, 1 if down else 0)

    def release_all(self):
        for k in KEYS:
            self.key(k, False)

    def joy(self, up=0, down=0, left=0, right=0, fire=0):
        v = 0x3F & ~((up << 0) | (down << 1) | (left << 2) | (right << 3) | (fire << 4))
        self.L.emu_set_joy(v)

    def det_r(self, on=True, seed=12345):
        self.L.emu_set_det_r(1 if on else 0, seed)

    def psg(self):
        p = self.L.emu_psg()
        return [p[i] for i in range(16)]

    # stats
    def exec_map(self):
        return bytes(C.cast(self.L.emu_exec_map(), C.POINTER(C.c_uint8 * 65536)).contents)

    def read_map(self):
        return bytes(C.cast(self.L.emu_read_map(), C.POINTER(C.c_uint8 * 65536)).contents)

    def write_map(self):
        return bytes(C.cast(self.L.emu_write_map(), C.POINTER(C.c_uint8 * 65536)).contents)

    def clear_maps(self):
        self.L.emu_clear_maps()

    def ix_filter(self, lo, hi):
        self.L.emu_ix_filter(lo, hi)

    def ix_exec(self):
        h = C.cast(self.L.emu_ix_exec(), C.POINTER(C.c_uint32 * 65536)).contents
        return {i: h[i] for i in range(65536) if h[i]}

    def watch(self, lo, hi, on=1):
        m = self.L.emu_watch_map()
        for a in range(lo, hi):
            m[a] = on

    def rwatch(self, lo, hi, on=1):
        m = self.L.emu_rwatch_map()
        for a in range(lo, hi):
            m[a] = on

    def rwatch_hist(self):
        h = C.cast(self.L.emu_rwatch_hist(), C.POINTER(C.c_ulong * 65536)).contents
        return {i: h[i] for i in range(65536) if h[i]}

    def watch_hist(self):
        h = C.cast(self.L.emu_watch_hist(), C.POINTER(C.c_ulong * 65536)).contents
        return {i: h[i] for i in range(65536) if h[i]}

    def viol(self):
        pcs = (C.c_uint16 * 64)(); ns = (C.c_ulong * 64)()
        n = self.L.emu_viol_list(pcs, ns)
        return dict(active=self.L.emu_viol(0), vblank=self.L.emu_viol(1), accesses=self.L.emu_viol(2), min_gap=self.L.emu_viol(3),
                    pcs={pcs[i]: ns[i] for i in range(n)})

    def viol_reset(self):
        self.L.emu_viol_reset()

    def screenshot(self, path, scale=2):
        buf = (C.c_uint8 * (256 * 192 * 3))()
        self.L.emu_render(buf)
        im = Image.frombytes('RGB', (256, 192), bytes(buf))
        if scale != 1:
            im = im.resize((256 * scale, 192 * scale), Image.NEAREST)
        im.save(path)
        return im
