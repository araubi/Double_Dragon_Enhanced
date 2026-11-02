import random, numpy as np
from PIL import Image
import coverage as C, equiv as E, mockup as M
from ramgame import RamGame
from msx import MSX
PAL=np.array([(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),(252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)],np.uint8)
def capture(g, mission):
    m=g.m; p19,p09=M.stores(mission); figs=[]; bg=None
    while True:
        pc=g.run_until([p19,p09,M.MARK,C.FRAME],100_000_000)
        if pc==C.FRAME: break
        if pc==M.MARK:
            if bg is None: bg=bytes(m.peek(a) for a in range(0x2C00,0x4000))
            figs.append([])
        else:
            de=m.get('de')
            if pc==p19: hl=m.get('hl'); mk=m.peek(hl-1); d=m.peek(hl); cov=(~mk|d)&255; ink=d
            else: bc=m.get('bc'); cov=(~(bc>>8))&255; ink=(bc&255)&cov
            if not figs: figs.append([])
            figs[-1].append((de,cov,ink))
        m.run(1)
    ret=m.peekw(m.get('sp')); m.run(1); g.run_until([ret])
    shot=np.array(m.screenshot('shots/_t.png',1))
    if bg is None: bg=bytes(m.peek(a) for a in range(0x2C00,0x4000))
    img=shot.copy(); vr=bytes(m.vram)
    for y in range(160):
        row,line=y>>3,y&7
        for cx in range(32):
            b=bg[row*256+line*32+cx]; ink=vr[0x2200+(row*32+cx)*8+line]>>4
            for k in range(8):
                img[16+y,cx*8+k]=PAL[ink] if b>>(7-k)&1 else (0,0,0)
    figs=[M.to_pixels(f) for f in figs if f]
    return img, [f for f in figs if f[1]]
def scale_fig(cov,ink,s):
    xs=[p[0] for p in cov|ink]; ys=[p[1] for p in cov|ink]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys); w,h=x1-x0+1,y1-y0+1
    if s=='w16': sx=min(1,16/w); sy=sx
    else: sx=sy=s
    nw,nh=max(1,round(w*sx)),max(1,round(h*sy))
    def im(pts):
        a=np.zeros((h,w),np.uint8)
        for x,y in pts: a[y-y0,x-x0]=255
        return np.array(Image.fromarray(a).resize((nw,nh),Image.NEAREST))>0
    cx=(x0+x1)//2; nx0=cx-nw//2; ny0=y1+1-nh
    def back(a): return {(nx0+x,ny0+y) for y,x in zip(*np.nonzero(a))}
    return back(im(cov)),back(im(ink))
def tiles(pts):
    if not pts: return []
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; x0,y0=min(xs),min(ys); t={}
    for x,y in pts: t.setdefault(((x-x0)//16,(y-y0)//16),set()).add((x,y))
    return [(x0+a*16,y0+b*16,p) for (a,b),p in t.items()]
def compose(img,figs,s,layers,rot):
    out=img.copy(); per=[]
    for cov,ink in figs:
        c,i=(cov,ink) if s==1 else scale_fig(cov,ink,s)
        if layers==1:
            for x,y in c:
                if 16<=y<176 and 0<=x<256: out[y,x]=(0,0,0)
            per.append([(t,(255,255,255)) for t in tiles(i)])
        else:
            per.append([(t,(255,255,255)) for t in tiles(i)]+[(t,(0,0,0)) for t in tiles(c-i)])
    if per: per=per[rot%len(per):]+per[:rot%len(per)]
    spr=[x for f in per for x in f]; shown=spr[:32]
    lines={}
    for k,((sx,sy,p),col) in enumerate(shown):
        for y in range(sy,sy+16): lines.setdefault(y,[]).append(k)
    vis={}
    for y,l in lines.items():
        for k in l[:4]: vis.setdefault(k,set()).add(y)
    tot=sum(len(p) for (sx,sy,p),c in spr); lost=sum(len(p) for (sx,sy,p),c in spr[32:])
    for k,((sx,sy,p),col) in enumerate(shown):
        for x,y in p:
            if y in vis.get(k,()) and 0<=y<192 and 0<=x<256: out[y,x]=col
            else: lost+=1
    return out, (lost/tot if tot else 0), len(spr)
