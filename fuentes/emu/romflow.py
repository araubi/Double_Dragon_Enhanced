import random, os, sys
from rommachine import machine
import coverage as C
DD='../dd'; B='../build'
MIS={n:open(os.path.join(B,'missions','m%d.bin'%n),'rb').read() for n in range(1,8)}
STUB={n:open(os.path.join(DD,'b%02d.bin'%k),'rb').read()[1:1+0x96] for n,k in zip(range(2,8),(8,10,12,14,16,18))}
EXTRA=open(os.path.join(DD,'b20.bin'),'rb').read()[1:1+0x550]
class Mon:
    """run_until wrapper that verifies every ROMLOAD request."""
    def __init__(self,m): self.m=m; self.log=[]; self.errors=[]
    def run_until(self,addrs,max_cycles=600_000_000):
        m=self.m; stops=set(addrs)|{0x0559,0x0EA60}
        end=m.cyc+max_cycles
        while m.cyc<end:
            if not m.run_until(stops,end-m.cyc): return None
            pc=m.get('pc')
            if pc==0x0559 and self._page0ram():
                ix,de=m.get('ix'),m.get('de'); m13=m.peek(0x5B13); e60=m.peek(0xEA60)
                ret=m.peekw(m.get('sp'))
                m.run(1); r=m.run_until([ret,0xEA60],100_000_000); pc2=m.get('pc')
                if pc2==0xEA60:
                    self.log.append(('COLD',hex(ix),hex(de))); 
                    if 0xEA60 in addrs: return pc2
                    continue
                exp={(0xEA60,0x96):lambda: STUB.get(m13+1),(0x9056,0x50F6):lambda: MIS.get(e60),(0xEE48,0x550):lambda: EXTRA}.get((ix,de),lambda:None)()
                got=bytes(m.peek(ix+i) for i in range(de))
                ok= exp is not None and got==exp
                self.log.append(('LOAD',hex(ix),hex(de),'ok' if ok else 'BAD'))
                if not ok: self.errors.append(self.log[-1])
                if pc2 in addrs: return pc2
                continue
            if pc in addrs: return pc
            m.run(1)
        return None
    def _page0ram(self):
        return (self.m.L.emu_get_ppiA() & 3) != 0   # page 0 not the BIOS slot
