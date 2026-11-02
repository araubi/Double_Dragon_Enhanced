import coverage as C, equiv as E, random
from ramgame import RamGame
def run(img,bf,seed=31,trials=8,shots=None):
    g=RamGame(open(img,'rb').read(), det_seed=seed, blockfn=bf); rnd=random.Random(seed); m=g.m
    C.boot(g)
    for ms in (1,2,3): C.play(g,20,rnd); C.complete_and_next(g,ms)
    A=0xAF45; P=0xAF21; res=[]; f=0; frames=[]
    while len(res)<trials and f<6000:
        f+=1
        if f%5==0:
            m.release_all()
            for k in rnd.choice([('RET','LEFT'),('RET','RIGHT'),('LEFT',),('RIGHT',),('UP',),('DOWN',)]): m.key(k)
        g.run_until([C.FRAME]); m.poke(0x5B08,5); m.poke(P+17,0x96); m.run(1)
        if m.peek(A+15)==3 and m.peek(A+9)==0x3C:
            m.release_all()
            # put player 1 right next to him, standing, same depth
            m.poke(P+3,(m.peek(A+3)+2)&255); m.poke(P+4,m.peek(A+4)); m.poke(P+9,0); m.poke(P+8,0)
            hist=[]
            for k in range(22):
                g.run_until([C.FRAME]); m.poke(0x5B08,5); m.run(1)
                hist.append((m.peek(A+9),m.peek(P+9)))
                if shots is not None and len(res)==0: frames.append(m.screenshot('shots/_a.png',1))
            got_up=any(a==0x32 for a,p in hist)
            thrown=any(p in (0x3D,0x3E,0x3C) for a,p in hist)
            res.append((got_up,thrown,' '.join('%02X/%02X'%h for h in hist)))
            for k in range(25): g.run_until([C.FRAME]); m.poke(0x5B08,5); m.poke(P+17,0x96); m.run(1)
    return res,frames
if __name__=='__main__':
    for name,img,bf in (('original','../dd/mem.bin',None),('nueva','../build/patched_mem.bin',E.pblk)):
        res,_=run(img,bf)
        print(name,'- se levanta con el jugador al lado: %d veces, jugador derribado: %d'%(sum(r[0] for r in res),sum(r[0] and r[1] for r in res)))
        for r in res[:3]: print('   estados Abobo/jugador:',r[2])
