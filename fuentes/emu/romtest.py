import random, sys, os
from rommachine import machine
import coverage as C
B='../build'
MIS=[open(os.path.join(B,'missions',('rom_m%d.bin' if os.path.exists(os.path.join(B,'missions','rom_m1.bin')) else 'm%d.bin')%n),'rb').read() for n in range(1,8)]
class G:
    def __init__(self,m): self.m=m
    def run_until(self,addrs,max_cycles=300_000_000):
        return self.m.pc if False else (self.m.get('pc') if self.m.run_until(addrs,max_cycles) else None)
def ram_ok(m, mission):
    d=MIS[mission-1]
    return sum(1 for i in range(len(d)) if m.peek(0x9056+i)!=d[i])
def boot(g):
    m=g.m
    assert g.run_until([0x0D03],600_000_000)==0x0D03
    m.key('SPACE'); m.run(3_000_000); m.key('SPACE',False)
    assert g.run_until([C.TITLE[1]])==C.TITLE[1]
    m.key('SPACE'); assert g.run_until([C.FRAME])==C.FRAME; m.key('SPACE',False)
def play(g,n,rnd):
    m=g.m
    for it in range(n):
        if it%6==0:
            m.release_all()
            for k in rnd.sample(C.KEYSET,3): m.key(k)
        assert g.run_until([C.FRAME],80_000_000)==C.FRAME
        m.poke(0x5B08,5); m.run(1)
def next_mission(g,mission):
    m=g.m; m.release_all()
    chk,flag=C.CHECK[mission]
    assert g.run_until([chk])==chk; m.poke(flag,1)       # completada: la siguiente se carga sola
    nxt=mission+1
    if nxt in C.TITLE:
        assert g.run_until([C.TITLE[nxt]],600_000_000)==C.TITLE[nxt]
    else:   # mission 7 has its own title code: wait until its data + extra block are in
        assert g.run_until([0x9056],600_000_000)==0x9056
        m.run(20_000_000)
    g.loaded_diff=ram_ok(m,nxt)
    m.key('SPACE'); assert g.run_until([C.FRAME],400_000_000)==C.FRAME; m.key('SPACE',False)
def test_layout(layout, rom, frames=60, seed=3):
    m=machine(rom,layout); g=G(m); rnd=random.Random(seed)
    boot(g)
    res=[]
    for mission in range(1,8):
        play(g,frames,rnd)
        res.append(getattr(g,'loaded_diff',ram_ok(m,1)) if mission>1 else 'boot')
        m.screenshot('shots/rom%s_m%d.png'%(layout,mission),1)
        if mission<7: next_mission(g,mission)
    return m,g,res
if __name__=='__main__':
    rom=open(os.path.join(B,'DoubleDragon_ASCII8.rom'),'rb').read()
    for lay in sys.argv[1:] or ['A','B','C']:
        m,g,res=test_layout(lay,rom)
        print('layout',lay,'bytes differing from mission block right after load (title screen):',res,'final A8=%02X'%m.L.emu_get_ppiA())
