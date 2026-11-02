import coverage as C, equiv as E, random, sys
from ramgame import RamGame
seed=int(sys.argv[1])
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=seed, blockfn=E.pblk); m=g.m; rnd=random.Random(seed)
m.viol_reset()
C.boot(g); out=[]
for ms in range(1,8):
    p1=m.peek(0x1C92)|m.peek(0x1C93)<<8; jeffs=0; seen=set()
    for f in range(700):
        if f%4==0:
            m.release_all()
            for k in rnd.choice([('RIGHT',),('RIGHT',),('SPACE','RIGHT'),('SPACE','LEFT'),('SPACE',),('UP',),('DOWN',),('LEFT',),('SPACE','UP'),('SPACE',)]): m.key(k)
        assert g.run_until([C.FRAME],100_000_000)==C.FRAME, ('hang',ms,f)
        m.poke(0x5B08,5); m.poke(p1+17,0x96)
        for k in (2,3,4):
            a=p1+18*k
            if m.peek(a) and m.peek(a+15)==0: seen.add((k,m.peek(a+17)))
        m.run(1)
    out.append('m%d ok jeff-slots=%d'%(ms,len(seen)))
    if ms<7: C.complete_and_next(g,ms)
v=m.viol(); print(seed,out,'VDP viol',v['active'],'min_gap',v['min_gap'])
