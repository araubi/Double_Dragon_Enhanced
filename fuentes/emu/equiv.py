"""Lock-step equivalence test: original vs patched image, identical inputs per frame."""
import random, sys, os
from ramgame import RamGame, blk
import coverage as C
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','build')
MAPK={9:2,11:3,13:4,15:5,17:6,19:7}
def pblk(k):
    if k in MAPK: return b'\x00'+open(os.path.join(B,'missions','m%d.bin'%MAPK[k]),'rb').read()
    return blk(k)
import functools
@functools.lru_cache(None)
def excl(mission):
    k=(6,9,11,13,15,17,19)[mission-1]
    o=blk(k)[1:1+0x50F6]; n=open(os.path.join(B,'missions','m%d.bin'%mission),'rb').read()
    return frozenset(0x9056+i for i in range(len(o)) if o[i]!=n[i])
TEXT_WIN={1:(0x91CE,0x91E8),2:(0x920F,0x922A),3:(0x9211,0x922C),4:(0x91FF,0x9219),5:(0x9219,0x9234),6:(0x9211,0x922C),7:(0,0)}
def frame(g, keys):
    m=g.m; m.release_all()
    for k in keys: m.key(k)
    pc=g.run_until([C.FRAME], 80_000_000); assert pc==C.FRAME
    m.poke(0x5B08,5)
    ret=m.peekw(m.get('sp')); c0=m.cyc
    m.run(1); pc=g.run_until([ret], 80_000_000); assert pc==ret
    return m.cyc-c0
def run(frames_per_mission=400, seed=5, missions=7, verbose=True):
    A=RamGame(open('../dd/mem.bin','rb').read(), det_seed=seed)
    Bg=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=seed, blockfn=pblk)
    for g in (A,Bg): C.boot(g)
    rnd=random.Random(seed); stats=[]
    A.m.viol_reset(); Bg.m.viol_reset()
    for mission in range(1,missions+1):
        tA=tB=0; bA=bB=0; mism=0
        cA0,cB0=A.m.cyc,Bg.m.cyc
        for f in range(frames_per_mission):
            keys=rnd.sample(C.KEYSET,3) if f%6==0 else keys
            bA+=frame(A,keys); bB+=frame(Bg,keys)
            va=bytes(A.m.vram); vb=bytes(Bg.m.vram)
            if va[:0x1800]!=vb[:0x1800] or va[0x2000:0x3800]!=vb[0x2000:0x3800]:
                mism+=1
                if mism<3:
                    d=[i for i in range(0x3800) if va[i]!=vb[i]]
                    print('  VRAM mismatch mission',mission,'frame',f,'n=',len(d),'first',[hex(x) for x in d[:8]])
            lo,hi=TEXT_WIN[mission]
            ra=bytes(A.m.peek(a) for a in range(0x4000,0xE14C) if not a in excl(mission) and not 0x5B20<=a<0x5B54) if f%50==0 else None
            if ra is not None:
                rb=bytes(Bg.m.peek(a) for a in range(0x4000,0xE14C) if not a in excl(mission) and not 0x5B20<=a<0x5B54)
                if ra!=rb:
                    d=[i for i in range(len(ra)) if ra[i]!=rb[i]]
                    print('  RAM mismatch mission',mission,'frame',f,len(d)); mism+=1
        tA=A.m.cyc-cA0; tB=Bg.m.cyc-cB0
        stats.append((mission,tA/frames_per_mission,tB/frames_per_mission,bA/frames_per_mission,bB/frames_per_mission,mism))
        if verbose: print('mission %d: T/frame orig %.0f -> new %.0f (x%.2f) | blit %.0f -> %.0f | mismatches %d'%(mission,tA/frames_per_mission,tB/frames_per_mission,tA/tB,bA/frames_per_mission,bB/frames_per_mission,mism))
        if mission<missions:
            for g in (A,Bg): C.complete_and_next(g,mission)
    return A,Bg,stats
if __name__=='__main__':
    A,Bg,st=run(int(sys.argv[1]) if len(sys.argv)>1 else 300)
    print('VDP orig',{k:v for k,v in A.m.viol().items() if k!='pcs'})
    print('VDP new ',Bg.m.viol())
