import coverage as C, equiv as E, random, pickle
from ramgame import RamGame
from PIL import Image
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=11, blockfn=E.pblk); m=g.m; rnd=random.Random(11)
C.boot(g)
NAMES=['1','2','3A','3B','4','5A','5B']
crops={}
for ms in range(1,8):
    p1=m.peek(0x1C92)|m.peek(0x1C93)<<8
    for f in range(1800):
        if f%4==0:
            m.release_all()
            for k in rnd.choice([('RIGHT',),('RIGHT',),('RET','RIGHT'),('RET','LEFT'),('RET',),('UP',),('DOWN',),('LEFT',),('RIGHT','UP'),('RIGHT','DOWN')]): m.key(k)
        g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+18+17,0x96)
        if f%6==0:
            figs=[]
            for k in range(8):
                a=p1+18*k
                if m.peek(a)==0 or m.peek(a+3)>40: continue
                figs.append((k,a,m.peek(a+3),m.peek(a+4),(m.peek(a+1),m.peek(a+2),m.peek(a+14),m.peek(a+15),m.peek(a+16)),m.peek(a+9)))
            for (k,a,X,Y,t,s) in figs:
                if k<2: continue
                if any(abs(X-X2)<6 and abs(Y-Y2)<5 for (k2,_,X2,Y2,_,_) in figs if k2!=k): continue
                key=(ms,t); lst=crops.setdefault(key,[])
                if len(lst)>=4 or any(c[0]==s for c in lst): continue
                m.screenshot('enem/tmp.png',1); im=Image.open('enem/tmp.png').convert('RGB')
                box=(max(0,8*X-16),max(16,8*Y),min(256,8*X+48),min(176,8*Y+72))
                if box[3]-box[1]<24 or box[2]-box[0]<24: continue
                lst.append((s,im.crop(box).copy(),X,Y,f,bytes(m.peek(a+i) for i in range(18))))
        m.run(1)
    print('mision',NAMES[ms-1],{t:len(v) for (mm,t),v in crops.items() if mm==ms},flush=True)
    if ms<7: C.complete_and_next(g,ms)
pickle.dump({k:[(s,c.tobytes(),c.size,X,Y,f,r) for (s,c,X,Y,f,r) in v] for k,v in crops.items()},open('enem/crops.pkl','wb'))
