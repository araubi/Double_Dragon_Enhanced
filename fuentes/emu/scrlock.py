import coverage as C, equiv as E, random, sys
from ramgame import RamGame
img,bf=(('../dd/mem.bin',None) if sys.argv[1]=='orig' else ('../build/patched_mem.bin',E.pblk))
ms_t=int(sys.argv[2])
g=RamGame(open(img,'rb').read(), det_seed=5, blockfn=bf); m=g.m; rnd=random.Random(5)
C.boot(g)
for ms in range(1,ms_t): C.play(g,20,rnd); C.complete_and_next(g,ms)
P1=[0xAE5D,0xAF52,0xAF2D,0xAF21,0xAF71,0xAEF4,0xAC63]; p1=P1[ms_t-1]
xs=[]
for f in range(150):
    m.release_all(); m.key('RIGHT')
    g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if f%10==0: xs.append('%02X'%m.peek(p1+3))
    m.run(1)
print(sys.argv[1],ms_t,' '.join(xs))
