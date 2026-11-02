import coverage as C, equiv as E, random, sys, collections
from ramgame import RamGame
seed=int(sys.argv[1])
TAB={1:0x97AD,2:0x9888,3:0x986C,4:0x9860,5:0x98AF,6:0x983F,7:0x9946}
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=seed, blockfn=E.pblk); m=g.m; rnd=random.Random(seed)
C.boot(g); res={}
for ms in range(1,8):
    p1=m.peek(0x1C92)|m.peek(0x1C93)<<8; hit=m.peek(0x1C94)|m.peek(0x1C95)<<8
    t=TAB[ms]; base=m.peek(t+1)|m.peek(t+2)<<8
    cnt=collections.Counter()
    for f in range(900):
        if f%4==0:
            m.release_all()
            for k in rnd.choice([('RIGHT',),('RET','RIGHT'),('RET','LEFT'),('RET',),('UP',),('DOWN',),('LEFT',),('RET','UP'),('SPACE',),('RET','DOWN')]): m.key(k)
        r=g.run_until([C.FRAME,hit],100_000_000)
        while r==hit:
            ix=m.get('ix'); de=m.get('de')
            who='jugador' if ix in (p1,p1+18) else 'tipo%d'%m.peek(ix+15)
            idx=(de-base)//3 if 0<=de-base<60 and (de-base)%3==0 else 'esp%04X'%de
            cnt[(who,'%02X'%m.peek(ix+9),idx,bytes(m.peek(de+i) for i in range(3)).hex())]+=1
            m.run(1); r=g.run_until([C.FRAME,hit],100_000_000)
        m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96); m.run(1)
    res[ms]=cnt
    if ms<7: C.complete_and_next(g,ms)
import pickle; pickle.dump(res,open('enem/hits%d.pkl'%seed,'wb'))
for ms,c in res.items(): print(ms,sorted(c.items()))
