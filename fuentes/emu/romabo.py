# Uso: CBIOS_DIR=... AX=14 python3 romabo.py ../build/DoubleDragon_ASCII8.rom fall|die|stand  -> shots/rab/*.png
# Misión 1 de la ROM: tumba (fall) o mata (die) al primer Abobo y guarda un cuadro por fotograma.
import sys,os,random
sys.path.insert(0,os.getcwd())
import romtest, coverage as C
from rommachine import machine
from PIL import Image
rom=open(sys.argv[1],'rb').read(); mode=sys.argv[2]
m=machine(rom,'A'); m.det_r(True,1); g=romtest.G(m); rnd=random.Random(5)
assert g.run_until([0x0D03],600_000_000)==0x0D03
m.key('SPACE'); m.run(3_000_000); m.key('SPACE',False)
assert g.run_until([C.TITLE[1]])==C.TITLE[1]; m.run(3_000_000)
m.key('SPACE'); assert g.run_until([C.FRAME])==C.FRAME; m.key('SPACE',False)
p1=m.peekw(0x1C92)
def frame():
    assert g.run_until([C.FRAME])==C.FRAME; m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
a=None
for f in range(8000):
    if f%4==0:
        m.release_all()
        for k in rnd.choice([('RIGHT',),('RIGHT',),('SPACE','RIGHT'),('SPACE','LEFT'),('UP',),('DOWN',),('RIGHT','UP'),('RIGHT','DOWN')]): m.key(k)
    frame()
    for k in range(2,5):
        b=p1+18*k
        if m.peek(b) and m.peek(b+15)==3 and 4<m.peek(b+3)<26: a=b
        if m.peek(b) and m.peek(b+15)!=3 and m.peek(b+17)>2: m.poke(b+17,2)
        if m.peek(b) and (m.peek(b+15)&15)==1 and m.peek(b+9)!=0xFF and f%90==89: m.poke(b+9,0xFF); m.poke(b+8,0x10); m.poke(b+17,0)
    m.run(1)
    if a: break
print('frame',f,'Abobo',hex(a)); m.release_all()
for f in range(200):
    frame()
    if m.peek(a+9)<0x30: break
    m.run(1)
AX=int(os.environ.get("AX","14")); m.poke(a+3,AX); m.poke(p1+3,(AX+10)&255); m.poke(p1+4,m.peek(a+4))
if len(sys.argv)>3: m.poke(a+16,int(sys.argv[3],16))
m.run(1); frame(); m.run(1); frame()
if mode=='fall': m.poke(a+9,0x3D); m.poke(a+8,0x0A); m.poke(a+17,60)
elif mode=='die':
    m.poke(a+17,5); m.poke(0x1DA8,0); m.poke(0x1DA9,10); m.poke(0x1DAA,10)
    sp=m.get('sp')-2; m.poke(sp,C.FRAME&255); m.poke(sp+1,C.FRAME>>8); m.set('sp',sp)
    m.set('ix',p1); m.set('iy',a); m.set('de',0x1DA8); m.set('pc',m.peekw(0x1C94))
    assert g.run_until([C.FRAME])==C.FRAME
os.makedirs('shots/rab',exist_ok=True)
rows=[]
def ixrun(tag):
    m.ix_filter(a,a+1); m.L.emu_ix_exec  # reset?
    m.run(1); frame(); m.run(1)
    h0=m.ix_exec(); frame(); h1=m.ix_exec()
    d={k:h1.get(k,0)-h0.get(k,0) for k in h1}; return {k for k,v in d.items() if v}
if os.environ.get('DBG'):
    lying=None
    for f in range(8):
        m.run(1); frame()
    m.run(1); frame(); m.run(1)
    m.rwatch(a,a+18); h0=m.rwatch_hist(); frame(); h1=m.rwatch_hist(); m.rwatch(a,a+18,0)
    A={k for k in h1 if h1[k]!=h0.get(k,0)}
    import pickle; pickle.dump(A,open('shots/rab/ix_%s.pkl'%os.environ['DBG'],'wb'))
    print('state',hex(m.peek(a+9)),len(A))
    v=m.vram; cells=[]
    for d in range(20):
        for e_ in range(32):
            for i in range(8):
                if v[0x200+d*256+e_*8+i]!=m.peek(0x2C00+d*256+e_+32*i): cells.append((d,e_)); break
    print('celdas distintas VRAM/búfer',len(cells),cells[:20])
    # dibuja el búfer como imagen
    from PIL import Image
    im=Image.new('L',(256,160))
    for d in range(20):
      for e_ in range(32):
        for i in range(8):
          b=m.peek(0x2C00+d*256+e_+32*i)
          for k in range(8): im.putpixel((e_*8+k,d*8+i),255 if b&(128>>k) else 0)
    im.save('shots/rab/buf_%s.png'%os.environ['DBG'])
    ref=open('../build/rom_mem.bin','rb').read()
    diff=[a_ for a_ in range(0x8000,0x9056) if m.peek(a_)!=ref[a_]]
    print('difs 8000-9055:',len(diff), ['%04X'%x for x in diff[:10]], ['%04X'%x for x in diff[-5:]])
    print('desc', ' '.join('%02X'%m.peek(0xAEED+i) for i in range(7*6)))
    e=m.peekw(0x9A0D); print('fin lista %04X'%e, ' '.join('%02X'%m.peek(e-40+i) for i in range(42)))
    m.clear_maps(); m.run(1); frame(); rm=m.read_map(); ex=m.exec_map()
    lo=e-40
    m.rwatch(lo,e+1); h0=m.rwatch_hist(); m.run(1); frame(); h1=m.rwatch_hist()
    print('lee lista:',sorted('%04X'%k for k in h1 if h1[k]!=h0.get(k,0)))
    sys.exit()
for f in range(40):
    m.run(1); frame()
    st=' '.join('%02X'%m.peek(a+i) for i in range(18))
    m.screenshot('shots/rab/%s_%02d.png'%(mode,f),1)
    rows.append(st)
m.poke(a,0)
for f in range(4): m.run(1); frame()
m.screenshot('shots/rab/bg.png',1)
bg=Image.open('shots/rab/bg.png').convert('RGB').crop((88,40,190,160)).tobytes()
for f,st in enumerate(rows):
    im=Image.open('shots/rab/%s_%02d.png'%(mode,f)).convert('RGB').crop((88,40,190,160)).tobytes()
    print(f,st,sum(1 for i in range(0,len(im),3) if im[i:i+3]!=bg[i:i+3]))
