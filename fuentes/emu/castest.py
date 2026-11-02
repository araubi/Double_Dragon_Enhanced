"""Run a CAS file through its own BLOAD block and turbo loader, with BIOS
TAPION/TAPIN/STMOTR emulated from the .cas contents."""
import os, functools
from msx import MSX
from rommachine import bios
from ramgame import basic_screen2
H=bytes([0x1F,0xA6,0xDE,0xBA,0xCC,0x13,0x7D,0x74])
def parse(cas):
    pos=[];i=0
    while (j:=cas.find(H,i))>=0: pos.append(j); i=j+8
    return [cas[p+8:(pos[k+1] if k+1<len(pos) else len(cas))] for k,p in enumerate(pos)]
class CasMachine:
    def __init__(self, cas_bytes):
        self.blocks=parse(cas_bytes)
        m=self.m=MSX(); m.add_rom(0,0,bios(),0); m.add_ram(3,0); m.slots(0); m.set('pc',0)
        m.run(3_579_545*4)                       # let C-BIOS initialise
        b3=self.blocks[3]; st=b3[0]|b3[1]<<8; en=b3[2]|b3[3]<<8; ex=b3[4]|b3[5]<<8
        for i,v in enumerate(b3[6:6+en-st+1]): m.poke(st+i,v)
        self.m.L.emu_set_slots(0xF0,0,0,0,0)
        basic_screen2(m)
        for i in range(0x3800): m.vram[i]=0       # BASIC SCREEN 2 is blank
        m.set('iff',0); m.set('sp',0xF0A0); m.set('pc',ex)
        self.blk=3; self.ptr=0; self.reads=[]; self.resets=0; self.motor=0
    def _bios0(self): return (self.m.L.emu_get_ppiA()&3)==0
    def run_until(self, addrs, max_cycles=2_000_000_000):
        m=self.m; stops=set(addrs)|{0x00E1,0x00E4,0x00F3,0x0000}; end=m.cyc+max_cycles
        while m.cyc<end:
            if not m.run_until(stops,end-m.cyc): return None
            pc=m.get('pc')
            if pc in (0x00E1,0x00E4,0x00F3,0x0000) and self._bios0():
                if pc==0x00E1:                     # TAPION: next block
                    self.blk+=1; self.ptr=0; self.reads.append(self.blk); m.set('af',0x0000)
                elif pc==0x00E4:                   # TAPIN
                    b=self.blocks[self.blk] if self.blk<len(self.blocks) else b''
                    if self.ptr<len(b): m.set('af',b[self.ptr]<<8); self.ptr+=1
                    else: m.set('af',0x0001)
                elif pc==0x00F3:
                    m.set('af',m.get('af')&0xFF00)
                else:
                    self.resets+=1; return 0
                m.ret(); continue
            if pc in addrs: return pc
            m.run(1)
        return None
