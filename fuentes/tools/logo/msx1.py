"""msx1.py SRC.png OUT.png [dither]: SCREEN 2 (2 colores por 8x1) con distancia CIELAB; con dither,
cada punto puede ser también la mezcla 50 % de los dos colores del bloque (tablero de ajedrez)"""
import sys, itertools
from PIL import Image
src=Image.open(sys.argv[1]).convert('RGB'); W,H=src.size; P=list(src.get_flattened_data() if hasattr(src,'get_flattened_data') else src.getdata())
DIT=len(sys.argv)>3 and sys.argv[3]!="0"
LW=float(sys.argv[4]) if len(sys.argv)>4 else 1
TMS=[(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),
     (252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)]
def lab(c):
    def f(v):
        v/=255; return ((v+0.055)/1.055)**2.4 if v>0.04045 else v/12.92
    r,g,b=map(f,c); X=(0.4124*r+0.3576*g+0.1805*b)/0.9505; Y=0.2126*r+0.7152*g+0.0722*b; Z=(0.0193*r+0.1192*g+0.9505*b)/1.089
    h=lambda t: t**(1/3) if t>0.008856 else 7.787*t+16/116
    return (116*h(Y)-16,500*(h(X)-h(Y)),200*(h(Y)-h(Z)))
L={}
def LB(c):
    if c not in L: L[c]=lab(c)
    return L[c]
def d(a,b):
    A,B=LB(a),LB(b); return LW*(A[0]-B[0])**2+(A[1]-B[1])**2+(A[2]-B[2])**2
C1=list(range(1,16))
out=[None]*(W*H); res=[]
for y in range(H):
    for bx in range(0,W,8):
        px=P[y*W+bx:y*W+bx+8]; best=None
        for a,b in itertools.combinations_with_replacement(C1,2):
            ca,cb=TMS[a],TMS[b]; mix=tuple((u+v)//2 for u,v in zip(ca,cb))
            e=0
            for c in px:
                v=min(d(c,ca),d(c,cb))
                if DIT and a!=b: v=min(v,d(c,mix)*1.15)
                e+=v
            if best is None or e<best[0]: best=(e,a,b)
        _,a,b=best; ca,cb=TMS[a],TMS[b]; mix=tuple((u+v)//2 for u,v in zip(ca,cb))
        for i,c in enumerate(px):
            x=bx+i; o=[(d(c,ca),a),(d(c,cb),b)]
            if DIT and a!=b: o.append((d(c,mix)*1.15,a if (x+y)&1 else b))
            out[y*W+x]=min(o)[1]
        res.append((a,b))
im=Image.new('RGB',(W,H)); im.putdata([TMS[k] for k in out]); im.save(sys.argv[2])
open(sys.argv[2][:-4]+'.idx','wb').write(bytes(out))
