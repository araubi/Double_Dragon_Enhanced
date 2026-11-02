import sys; sys.path.insert(0,'.')
import coverage as C, equiv as E, random
from ramgame import RamGame
from PIL import Image
mem=sys.argv[1]; out=sys.argv[2]
g=RamGame(open(mem,'rb').read(), det_seed=5, blockfn=E.pblk); m=g.m; rnd=random.Random(5)
C.boot(g)
for ms in range(1,5): C.play(g,20,rnd); C.complete_and_next(g,ms)
ims=[]
for f in range(2400):
    m.release_all(); m.key('RIGHT')
    if f%80<20: m.key('UP')
    g.run_until([C.FRAME],100_000_000); p1=m.peekw(0x1C92); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if f%20==0:
        for k in (2,3,4):
            a=p1+18*k
            if m.peek(a): m.poke(a+9,0xFF); m.poke(a+8,0x10); m.poke(a+17,0)
    if f%60==0:
        print(f,'B0FA %02X'%m.peek(0xB0FA),'C40E %02X'%m.peek(0xC40E),flush=True)
        m.run(1); g.run_until([C.FRAME],100_000_000); m.screenshot(out+'_%04d.png'%f,1)
    m.run(1)
