import coverage as C, equiv as E, random, sys
from ramgame import RamGame
from PIL import Image
img,bf=(('../dd/mem.bin',None) if sys.argv[1]=='orig' else ('../build/patched_mem.bin',E.pblk))
g=RamGame(open(img,'rb').read(), det_seed=5, blockfn=bf); m=g.m; rnd=random.Random(5)
C.boot(g); C.play(g,20,rnd); C.complete_and_next(g,1)
p1=0xAF52; ob=0xAFAC; got=None; shots=[]
for f in range(70): g.run_until([C.FRAME],100_000_000); m.run(1)
tmpl=bytes.fromhex('0a0202140a05b00000020000000000000000')
for f in range(500):
    m.release_all()
    for k in (2,3,4): m.poke(p1+18*k,0)
    if got is None:
        if f%30==0:
            m.poke(p1+3,0x10); m.poke(p1+4,0x0A-3-(f//30)%4); m.poke(p1+9,0)
            for i,v in enumerate(tmpl): m.poke(ob+i,v)
            m.poke(ob+3,0x0F); m.poke(ob+4,0x0A)
        if f%30 in (3,4,5): m.key('RET')
    else:
        m.key('LEFT' if ((f-got)//30)%2 else 'RIGHT')
    g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96)
    if got is None and m.peek(p1+7): got=f; print('cogido en',f,'y',m.peek(p1+4))
    if got is not None and (f-got)%5==2 and len(shots)<10:
        m.run(1); g.run_until([C.FRAME],100_000_000); m.screenshot('enem/tmp.png',1)
        X,Y=m.peek(p1+3),m.peek(p1+4); im=Image.open('enem/tmp.png').convert('RGB')
        shots.append(im.crop((8*X-24,8*Y-16,8*X+48,8*Y+72)).resize((144,176)))
    m.run(1)
W=Image.new('RGB',(10*150,180),(20,20,20))
for i,c in enumerate(shots): W.paste(c,(i*150,2))
W.save('enem/barrel_%s.png'%sys.argv[1]); print(len(shots))
