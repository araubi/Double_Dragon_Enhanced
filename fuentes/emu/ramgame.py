"""Boot the CAS version straight from a post-load memory image (skipping the tape),
with a tape-emulation trap on the loader entry (05B3h) for the multiload."""
import os
from msx import MSX

DD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dd')


def blk(k):
    return open(os.path.join(DD, 'b%02d.bin' % k), 'rb').read()


def basic_screen2(m):
    for r, v in enumerate([0x02, 0xE0, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x11]):
        m.set_vreg(r, v)
    vr = m.vram
    for i in range(768):
        vr[0x1800 + i] = i & 255
    for i in range(32):
        vr[0x1B00 + i * 4] = 0xD1
    scr = blk(4)[1:1 + 0x3000]
    for i in range(0x1800):
        vr[i] = scr[i]
        vr[0x2000 + i] = scr[0x1800 + i]


class RamGame:
    TAPE_AFTER_BOOT = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

    def __init__(self, memimage, loader_trap=0x05B3, det_seed=12345, blockfn=None):
        self.blockfn = blockfn or blk
        self.m = m = MSX()
        ram = m.add_ram(3)
        for i, b in enumerate(memimage):
            ram[i] = b
        m.slots(0xFF)
        basic_screen2(m)
        m.set('sp', 0x2710)
        m.set('pc', 0xEA60)
        m.set('iff', 0)
        m.det_r(True, det_seed)
        self.tape = list(self.TAPE_AFTER_BOOT)
        self.loader_trap = loader_trap
        self.loads = []

    def tape_trap(self):
        m = self.m
        ix, de = m.get('ix'), m.get('de')
        if not self.tape:
            raise RuntimeError('tape exhausted')
        k = self.tape.pop(0)
        d = self.blockfn(k)[1:1 + de]
        for i, b in enumerate(d):
            m.poke((ix + i) & 0xFFFF, b)
        self.loads.append((k, ix, de))
        m.set('af', 0x0001)   # A=0, carry
        m.ret()

    def run_until(self, addrs, max_cycles=200_000_000):
        """Run until one of addrs; services tape trap transparently."""
        addrs = set(addrs)
        stops = addrs | {self.loader_trap}
        end = self.m.cyc + max_cycles
        while self.m.cyc < end:
            hit = self.m.run_until(stops, end - self.m.cyc)
            if not hit:
                return None
            pc = self.m.get('pc')
            if pc == self.loader_trap and pc not in addrs:
                self.tape_trap()
                continue
            return pc
        return None
