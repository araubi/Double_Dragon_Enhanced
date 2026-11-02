"""msxfiles.py: ficheros BLOAD ,S para ver el logo en un MSX (o en openMSX con una carpeta como disco)"""
from PIL import Image
TMS=[(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),
     (252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)]
def bsave(name,start,data):
    end=start+len(data)-1
    open(name,'wb').write(bytes([0xFE,start&255,start>>8,end&255,end>>8,start&255,start>>8])+bytes(data))
def canvas(png,h,y0):
    im=Image.open(png).convert('RGB'); W,H=im.size
    c=Image.new('RGB',(256,h)); c.paste(im,(0,y0)); return c
# SCREEN 2: patrones 0000h, nombres 1800h (0-255 en cada tercio), colores 2000h
def sc2(png,out):
    c=canvas(png,192,9); px=c.load(); inv={v:i for i,v in reversed(list(enumerate(TMS)))}
    vram=bytearray(0x3800)
    for t in range(3):
        for i in range(256): vram[0x1800+t*256+i]=i
    for y in range(192):
        for bx in range(0,256,8):
            ks=[inv[px[bx+i,y]] for i in range(8)]
            u=sorted(set(ks),key=ks.count,reverse=True)
            fg=u[0]; bg=u[1] if len(u)>1 else 1
            if fg==1 and len(u)>1: fg,bg=bg,fg      # negro de fondo
            assert len(u)<=2,(y,bx,u)
            bits=0
            for k in ks: bits=bits<<1|(k==fg and k!=bg)
            ch=(y//64)*256+(bx//8)+(y%64//8)*32
            vram[ch*8+y%8]=bits; vram[0x2000+ch*8+y%8]=fg<<4|(bg if bg!=1 else 0)
    bsave(out,0,vram)
# SCREEN 5: 4 bits por punto, paleta en 7680h (COLOR=RESTORE)
def sc5(png,out):
    c=canvas(png,212,19); px=c.load()
    cols=[(0,0,0)]+sorted(set(px[x,y] for y in range(212) for x in range(256))-{(0,0,0)})
    assert len(cols)<=16,len(cols)
    idx={v:i for i,v in enumerate(cols)}
    vram=bytearray(0x76A0)
    for y in range(212):
        for x in range(0,256,2): vram[y*128+x//2]=idx[px[x,y]]<<4|idx[px[x+1,y]]
    for i,(r,g,b) in enumerate(cols):
        r,g,b=(round(v*7/255) for v in (r,g,b)); vram[0x7680+2*i]=r<<4|b; vram[0x7681+2*i]=g
    bsave(out,0,vram)
# SCREEN 8: GGGRRRBB
def sc8(png,out):
    c=canvas(png,212,19); px=c.load(); vram=bytearray(256*212)
    for y in range(212):
        for x in range(256):
            r,g,b=px[x,y]; vram[y*256+x]=round(g*7/255)<<5|round(r*7/255)<<2|round(b*3/255)
    bsave(out,0,vram)
sc2('m1_n2.png','LOGO1.SC2'); sc2('m1_d2.png','LOGO1D.SC2'); sc5('plata_msx2_sc5.png','LOGO2.SC5'); sc8('plata_msx2_sc8.png','LOGO2.SC8')
open('VER.BAS','w',newline='\r\n').write('\n'.join([
 '10 SCREEN 2:BLOAD"LOGO1.SC2",S:GOSUB 100',
 '20 SCREEN 2:BLOAD"LOGO1D.SC2",S:GOSUB 100',
 '30 SCREEN 5:BLOAD"LOGO2.SC5",S:COLOR=RESTORE:GOSUB 100',
 '40 SCREEN 8:BLOAD"LOGO2.SC8",S:GOSUB 100',
 '50 END',
 '100 IF INKEY$="" THEN 100 ELSE RETURN'])+'\n')
print('ok')
