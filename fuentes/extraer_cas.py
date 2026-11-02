"""Extrae del .cas original los bloques e imagen de memoria que usan los scripts de build.
uso: python3 extraer_cas.py "Double_Dragon_...cas" """
import sys, os
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'dd'); os.makedirs(D,exist_ok=True)
d=open(sys.argv[1],'rb').read(); open(os.path.join(D,'dd.cas'),'wb').write(d)
H=bytes([0x1F,0xA6,0xDE,0xBA,0xCC,0x13,0x7D,0x74]); pos=[]; i=0
while (j:=d.find(H,i))>=0: pos.append(j); i=j+8
assert len(pos)==21, 'se esperaban 21 bloques'
for k,p in enumerate(pos):
    e=pos[k+1] if k+1<len(pos) else len(d); open(os.path.join(D,'b%02d.bin'%k),'wb').write(d[p+8:e])
b3=open(os.path.join(D,'b03.bin'),'rb').read(); ld=b3[6:6+0xDB5E-0xC2D0+1]
open(os.path.join(D,'loader.bin'),'wb').write(ld)
mem=bytearray(65536); mem[0xC2D0:0xC2D0+len(ld)]=ld
o=0xC36B-0xC2D0; mem[0x556:0x556+0x1724]=ld[o:o+0x1724]
for k,a,n in ((4,0x9C40,0x3000),(5,0xE14C,0xEF5),(6,0x9056,0x50F6),(7,0x5B5E,0x34F0)):
    b=open(os.path.join(D,'b%02d.bin'%k),'rb').read(); mem[a:a+n]=b[1:1+n]
open(os.path.join(D,'mem.bin'),'wb').write(mem); print('ok:',D)
