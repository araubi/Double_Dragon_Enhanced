import coverage as C, equiv as E, random, sys
from ramgame import RamGame
ms_t=int(sys.argv[1]); FR=int(sys.argv[2])
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=3, blockfn=E.pblk); m=g.m; rnd=random.Random(3)
C.boot(g)
for ms in range(1,ms_t): C.play(g,20,rnd); C.complete_and_next(g,ms)
p1=m.peek(0x1C92)|m.peek(0x1C93)<<8
act={}; prev=[0]*8; snap=None; bad=[]
def buf(): return bytes(m.peek(0x2C00+i) for i in range(20*256))
SHOT=set(int(x) for x in sys.argv[4].split(',')) if len(sys.argv)>4 else set()
WATCH=int(sys.argv[3]) if len(sys.argv)>3 else -1
for f in range(FR):
    if f==WATCH: m.watch(0x2C00,0x4000)
    if f==WATCH+12: print('writers',sorted((hex(k),v) for k,v in m.watch_hist().items())); m.watch(0x2C00,0x4000,0)
    m.release_all(); m.key('RIGHT'); ph=f%160
    if 80<=ph<120: m.key('UP')
    elif ph>=120: m.key('DOWN')
    if f%7==0: m.key('RET')
    g.run_until([C.FRAME],100_000_000)
    if snap is not None:
        v=m.vram; n=0; cells=[]
        for d in range(20):
            for e in range(32):
                for i in range(8):
                    if v[0x200+d*256+e*8+i]!=snap[d*256+e+32*i]: n+=1; cells.append((d,e)); break
        if n: bad.append((f,n,cells[:6]))
        if n and f in SHOT:
            m.screenshot('enem/dirty_%d_%d.png'%(ms_t,f),1)
            import PIL.Image as I
            im=I.new('RGB',(256,160)); px=im.load()
            for d in range(20):
                for e in range(32):
                    for i in range(8):
                        b_=snap[d*256+e+32*i]
                        for x in range(8): px[e*8+x,d*8+i]=(255,255,255) if b_&(128>>x) else (0,0,0)
            im.save('enem/expect_%d_%d.png'%(ms_t,f))
    snap=buf()
    m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if m.peek(p1+18+9)<0x30: m.poke(p1+18+3,max(0,m.peek(p1+3)-3)); m.poke(p1+18+4,m.peek(p1+4))
    for k in (2,3,4):
        a=p1+18*k; on=m.peek(a)>=5 and m.peek(a+3)<0x20
        if on and not prev[k]: act[k]=f; print('f%d slot%d tipo %d'%(f,k,m.peek(a+15)),flush=True)
        prev[k]=on
        if on and f-act.get(k,f)>40 and m.peek(a+9)!=0xFF: m.poke(a+9,0xFF); m.poke(a+8,0x10); m.poke(a+17,0)
    m.run(1)
print('frames con celdas desfasadas:',len(bad))
for b in bad: print(b[0],b[1],b[2])
