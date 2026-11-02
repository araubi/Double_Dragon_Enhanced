"""Option-1 mock-up: figures' ink layer as 1-colour 16x16 hardware sprites (white),
black mask kept in the bitmap. Captures real frames, applies TMS9918 limits
(4 sprites/line, 32 total) with per-frame priority rotation (multiplexing)."""
import random, re, os, sys
import numpy as np
from PIL import Image
import coverage as C, equiv as E
from ramgame import RamGame
SYM={l.split(':')[0]:int(l.split('0x')[1],16) for l in open('../build/dd_ram.sym') if 'EQU 0x' in l}
MARK=SYM['MARK']
def stores(mission):
    b=open('../build/missions/m%d.bin'%mission,'rb').read()
    p19=0x9056+b.find(bytes.fromhex('1aa623b612c9'))+4
    p09=0x9056+b.find(bytes.fromhex('1aa0b112c1c9'))+3
    return p19,p09
def capture(g, mission):
    """run one game frame; return list of figures [(dest,covered,ink),...] and screenshot RGB"""
    m=g.m; p19,p09=stores(mission)
    figs=[]
    while True:
        pc=g.run_until([p19,p09,MARK,C.FRAME],100_000_000)
        if pc==C.FRAME: break
        if pc==MARK: figs.append([])
        else:
            de=m.get('de')
            if pc==p19:
                hl=m.get('hl'); mk=m.peek(hl-1); d=m.peek(hl); cov=(~mk|d)&255; ink=d
            else:
                bc=m.get('bc'); b=bc>>8; c=bc&255; cov=(~b)&255; ink=c&cov
            if not figs: figs.append([])
            figs[-1].append((de,cov,ink))
        m.run(1)
    # let the blit run, then grab the screen
    ret=m.peekw(m.get('sp')); m.run(1); g.run_until([ret]); 
    buf=np.zeros((16+192,256,3),np.uint8)
    im=np.array(g.m.screenshot('shots/_tmp.png',1))
    return figs, im
def to_pixels(fig):
    cov=set(); ink=set()
    for de,cv,ik in fig:
        o=de-0x2C00
        if not 0<=o<0x1400: continue
        row,line,col=o>>8,(o>>5)&7,o&31
        y=16+row*8+line; x0=col*8
        for b in range(8):
            if cv>>(7-b)&1: cov.add((x0+b,y))
            if ik>>(7-b)&1: ink.add((x0+b,y))
    return cov,ink
def sprites_for(ink):
    if not ink: return []
    xs=[p[0] for p in ink]; ys=[p[1] for p in ink]; x0,y0=min(xs),min(ys)
    tiles={}
    for x,y in ink: tiles.setdefault(((x-x0)//16,(y-y0)//16),set()).add((x,y))
    return [(x0+tx*16,y0+ty*16,pix) for (tx,ty),pix in sorted(tiles.items())]
def render(im, figs, rot):
    out=im.copy(); allspr=[]
    per=[]
    for f in figs:
        cov,ink=to_pixels(f)
        for x,y in cov: out[y,x]=(0,0,0)
        per.append(sprites_for(ink))
    order=per[rot%len(per):]+per[:rot%len(per)] if per else []
    for s in order: allspr+=s
    shown=allspr[:32]; dropped_total=len(allspr)-len(shown)
    lines={}
    lost=0; over_lines=0
    for i,(sx,sy,pix) in enumerate(shown):
        for y in range(sy,sy+16): lines.setdefault(y,[]).append(i)
    vis={}
    for y,l in lines.items():
        if len(l)>4: over_lines+=1
        for i in l[:4]: vis.setdefault(i,set()).add(y)
    for i,(sx,sy,pix) in enumerate(shown):
        for x,y in pix:
            if y in vis.get(i,()) and 0<=y<192: out[y,x]=(255,255,255)
            else: lost+=1
    tot=sum(len(p) for _,_,p in allspr)
    return out, dict(sprites=len(allspr),over_lines=over_lines,lost_px=lost+sum(len(p) for _,_,p in allspr[32:]),ink_px=tot)
def run(mission, nframes=120, seed=11, keyframes=()):
    g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=seed, blockfn=E.pblk); rnd=random.Random(seed)
    C.boot(g)
    for ms in range(1,mission): C.play(g,20,rnd); C.complete_and_next(g,ms)
    C.play(g,40,rnd)
    stats=[]; shots=[]
    for f in range(nframes):
        if f%6==0:
            g.m.release_all()
            for k in rnd.sample(C.KEYSET,3): g.m.key(k)
        figs,im=capture(g,mission)
        figs=[x for x in figs if x]
        a,s=render(im,figs,0); b,_=render(im,figs,1)
        s['figs']=len(figs); stats.append(s)
        if f in keyframes: shots.append((im,a,b,s))
        g.m.poke(0x5B08,5)
    return stats,shots
