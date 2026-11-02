import coverage as C, equiv as E, random, pickle, sys
from ramgame import RamGame
from PIL import Image
ms_target=int(sys.argv[1]); FR=int(sys.argv[2]); KILL=int(sys.argv[3]) if len(sys.argv)>3 else 0; FOLLOW=1
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=5, blockfn=E.pblk); m=g.m; rnd=random.Random(5)
C.boot(g)
for ms in range(1,ms_target): C.play(g,20,rnd); C.complete_and_next(g,ms)
p1=m.peek(0x1C92)|m.peek(0x1C93)<<8
prev=[0]*8; spawn=[None]*8; out=[]
for f in range(FR):
    if f%4==0:
        m.release_all()
        for k in rnd.choice([('RIGHT',),('RIGHT',),('RET','RIGHT'),('RET','LEFT'),('RET',),('UP',),('DOWN',),('RIGHT','UP'),('RIGHT','DOWN')]): m.key(k)
    r=g.run_until([C.FRAME],100_000_000)
    m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if FOLLOW and m.peek(p1+18+9)<0x30: m.poke(p1+18+3,max(0,m.peek(p1+3)-3))
    for k in range(2,8):
        a=p1+18*k; act=m.peek(a)
        if act and not prev[k]:
            spawn[k]=dict(f=f,k=k,raw=bytes(m.peek(a+i) for i in range(18)),crop=None,n=0); out.append(spawn[k])
        prev[k]=act
        if act and m.peek(a+17)>2: m.poke(a+17,2)
        if KILL and act and spawn[k] and f-spawn[k]['f']>KILL and (m.peek(a+15)&15) in (1,2,3) and m.peek(a+9)!=0xFF:
            m.poke(a+9,0xFF); m.poke(a+8,0x10); m.poke(a+17,0)
        sp=spawn[k]
        if act and sp and sp['n']<3 and m.peek(a+9)==0 and f%3==0:
            X,Y=m.peek(a+3),m.peek(a+4)
            others=[(m.peek(p1+18*j+3),m.peek(p1+18*j+4)) for j in range(8) if j!=k and m.peek(p1+18*j)]
            if X<=26 and 2<=Y<=12 and not any(abs(X-x)<6 and abs(Y-y)<5 for x,y in others):
                m.screenshot('enem/tmp.png',1); im=Image.open('enem/tmp.png').convert('RGB')
                sp.setdefault('crops',[]).append(im.crop((8*X-16,8*Y,8*X+48,8*Y+72)).tobytes()); sp['n']+=1
                sp['raw2']=bytes(m.peek(a+i) for i in range(18))
    if f%250==0: m.screenshot('enem/m%d_f%05d.png'%(ms_target,f),1)
    m.run(1)
print(len(out),'apariciones')
for s in out: print(s['f'],s['k'],s['raw'].hex(),s.get('raw2',b'').hex(),len(s.get('crops',[])))
pickle.dump(out,open('enem/spawns%d.pkl'%ms_target,'wb'))
