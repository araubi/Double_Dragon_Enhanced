import coverage as C, equiv as E, random, sys
from ramgame import RamGame
img,bf=(('../dd/mem.bin',None) if sys.argv[1]=='orig' else ('../build/patched_mem.bin',E.pblk))
g=RamGame(open(img,'rb').read(), det_seed=5, blockfn=bf); m=g.m; rnd=random.Random(5)
C.boot(g); p1=0xAE5D
SNAP=[None]; BAD=[]
def chk():
    if SNAP[0] is not None:
        v=m.vram; cells=[]
        for d in range(20):
            for e in range(32):
                for i in range(8):
                    if v[0x200+d*256+e*8+i]!=SNAP[0][d*256+e+32*i]: cells.append((d,e)); break
        if cells: BAD.append((m.peek(0xAE81+9),len(cells),cells[:4]))
    SNAP[0]=bytes(m.peek(0x2C00+i) for i in range(20*256))
def frame(keys=None):
    g.run_until([C.FRAME],100_000_000); chk(); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
# reach first Abobo with the same inputs as spawns.py
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
print('frame',f)
ab=[p1+18*k for k in range(2,5) if m.peek(p1+18*k) and m.peek(p1+18*k+15)==3]
print('Abobo slots',[hex(a) for a in ab]); a=ab[0]
import collections
for trial in range(4):
    # wait until Abobo is standing, then knock him down via the hit state
    for f in range(200):
        frame(); 
        if m.peek(a+9)<0x30: break
        m.run(1)
    m.poke(a+9,0x3D); m.poke(a+8,0x0A); m.poke(a+17,60)
    seq=[]; thrown=False; up=None
    for f in range(160):
        m.release_all(); frame()
        s_=m.peek(a+9); ps=m.peek(p1+9)
        if s_>=0x30 and ps<0x3C:
            m.poke(p1+3,(m.peek(a+3)+2)&0xFF); m.poke(p1+4,m.peek(a+4))
        if not seq or seq[-1][0]!=s_ or seq[-1][1]!=ps: seq.append((s_,ps))
        m.run(1)
    print(sys.argv[1],'prueba',trial,' '.join('%02X/%02X'%x for x in seq[:24]))
print('frames con celdas sin subir:',len(BAD)); [print('%02X'%b[0],b[1],b[2]) for b in BAD[20:]]
