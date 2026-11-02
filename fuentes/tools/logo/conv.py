"""conv.py SRC.png PREFIJO: logo de la recreativa a MSX1 (SCREEN 2) y MSX2 (SCREEN 5 y 8)"""
import sys, itertools, random
from PIL import Image
src=Image.open(sys.argv[1]).convert('RGB'); pre=sys.argv[2]
W,H=src.size; P=list(src.getdata())
def d2(a,b):
    r=(a[0]+b[0])/2; dr,dg,db=a[0]-b[0],a[1]-b[1],a[2]-b[2]
    return (2+r/256)*dr*dr+4*dg*dg+(2+(255-r)/256)*db*db
# ---- MSX1: paleta TMS9918 (la de openMSX), 2 colores por cada 8x1
TMS=[(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),
     (252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)]
C1=list(range(1,16))
out1=[0]*(W*H); pat=[]; col=[]
dist={}
def dd(c,k):
    key=(c,k)
    if key not in dist: dist[key]=d2(c,TMS[k])
    return dist[key]
for y in range(H):
    for bx in range(0,W,8):
        px=P[y*W+bx:y*W+bx+8]
        best=None
        for a,b in itertools.combinations_with_replacement(C1,2):
            e=sum(min(dd(c,a),dd(c,b)) for c in px)
            if best is None or e<best[0]: best=(e,a,b)
        _,a,b=best
        bits=0
        for i,c in enumerate(px):
            k=a if dd(c,a)<=dd(c,b) else b
            out1[y*W+bx+i]=k; bits=bits<<1|(k==a)
        pat.append(bits); col.append(a<<4|b)
im1=Image.new('RGB',(W,H)); im1.putdata([TMS[k] for k in out1]); im1.save(pre+'_msx1_sc2.png')
# ---- MSX2 SCREEN 5: 16 colores de 512 (3 bits por componente), el 0 negro
def q3(c): return tuple(round(v*7/255) for v in c)
def e3(c): return tuple(round(v*255/7) for v in c)
from collections import Counter
cnt=Counter(P)
cols=[c for c in cnt if c!=(0,0,0)]
# k-medias con peso, partiendo de los más frecuentes
random.seed(1)
cent=[c for c,_ in cnt.most_common() if c!=(0,0,0)][:15]
for it in range(40):
    grp={i:[] for i in range(15)}
    for c in cols:
        i=min(range(15),key=lambda i:d2(c,cent[i])); grp[i].append(c)
    new=[]
    for i in range(15):
        g=grp[i]
        if not g: new.append(cent[i]); continue
        w=sum(cnt[c] for c in g)
        new.append(tuple(sum(c[k]*cnt[c] for c in g)/w for k in range(3)))
    cent=new
pal=[(0,0,0)]+[q3(c) for c in cent]
palrgb=[e3(c) for c in pal]
idx=[0 if c==(0,0,0) else min(range(1,16),key=lambda i:d2(c,palrgb[i])) for c in P]
im5=Image.new('RGB',(W,H)); im5.putdata([palrgb[i] for i in idx]); im5.save(pre+'_msx2_sc5.png')
# ---- MSX2 SCREEN 8: 256 colores fijos GGGRRRBB
def s8(c):
    g=min(range(8),key=lambda v:abs(v*255/7-c[1])); r=min(range(8),key=lambda v:abs(v*255/7-c[0])); b=min(range(4),key=lambda v:abs(v*255/3-c[2]))
    return (round(r*255/7),round(g*255/7),round(b*255/3))
im8=Image.new('RGB',(W,H)); im8.putdata([s8(c) for c in P]); im8.save(pre+'_msx2_sc8.png')
# ---- ficheros para el MSX: SCREEN 2 (patrones/colores por bloque 8x8) y SCREEN 5 (4 bits por punto + paleta)
open(pre+'_sc5.pal','wb').write(bytes(b for c in pal for b in ((c[0]<<4)|c[2],c[1])))
sc5=bytearray()
for y in range(H):
    for x in range(0,W,2): sc5.append(idx[y*W+x]<<4|idx[y*W+x+1])
open(pre+'_sc5.bin','wb').write(sc5)
print('SC5 paleta (R,G,B 0-7):',pal)
