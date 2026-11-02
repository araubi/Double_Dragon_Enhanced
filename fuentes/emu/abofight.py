import coverage as C, equiv as E, random, sys
from ramgame import RamGame
img,bf=(('../dd/mem.bin',None) if sys.argv[1]=='orig' else ('../build/patched_mem.bin',E.pblk))
g=RamGame(open(img,'rb').read(), det_seed=5, blockfn=bf); m=g.m; rnd=random.Random(5)
C.boot(g); p1=0xAE5D
def frame():
    g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
for f in range(6000):
    if f%4==0:
        m.release_all()
        for k in rnd.choice([('RIGHT',),('RIGHT',),('RET','RIGHT'),('RET','LEFT'),('RET',),('UP',),('DOWN',),('RIGHT','UP'),('RIGHT','DOWN')]): m.key(k)
    frame()
    stop=False
    for k in range(2,5):
        a=p1+18*k
        if m.peek(a) and m.peek(a+15)==3 and m.peek(a+3)<30: stop=True
        if m.peek(a) and m.peek(a+17)>2: m.poke(a+17,2)
        if m.peek(a) and (m.peek(a+15)&15)==1 and m.peek(a+9)!=0xFF and f%90==89: m.poke(a+9,0xFF); m.poke(a+8,0x10); m.poke(a+17,0)
    if f%2==0 and m.peek(p1+18+9)<0x30: m.poke(p1+18+3,max(0,m.peek(p1+3)-3))
    m.run(1)
    if stop: break
ab=[p1+18*k for k in range(2,5) if m.peek(p1+18*k) and m.peek(p1+18*k+15)==3]; a=ab[0]
m.release_all()
for f in range(200):
    frame()
    if m.peek(a+9)<0x30: break
    m.run(1)
# move player away
m.poke(p1+3,(m.peek(a+3)+10)&255)
m.poke(a+9,0x3D); m.poke(a+8,0x0A); m.poke(a+17,60)
for f in range(40):
    frame()
    print(f,' '.join('%02X'%m.peek(a+i) for i in range(18)))
    m.screenshot('shots/fall_%s_%02d.png'%(sys.argv[1],f),2)
    m.run(1)
print('Abobo',hex(a))
log=[]
for f in range(400):
    m.release_all()
    if f%6<3: m.key('SPACE'); m.key('DOWN'); m.key('RET')
    frame()
    if m.peek(p1+9)<0x30 and f%6==0:
        m.poke(p1+3,(m.peek(a+3)-4)&255); m.poke(p1+4,m.peek(a+4))
    if len(sys.argv)<3 and m.peek(a+17)<20: m.poke(a+17,60)
    st=' '.join('%02X'%m.peek(a+i) for i in range(18))
    log.append(st)
    if 0x3B<=m.peek(a+9)<=0x3F or m.peek(a)==0: m.screenshot('shots/fight_%03d.png'%f,1)
    m.run(1)
prev=None
for f,s in enumerate(log):
    k=s[0:2]+' '+s[27:29]
    if k!=prev: print(f,s); prev=k
