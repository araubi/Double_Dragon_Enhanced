import coverage as C, equiv as E, random, sys
from ramgame import RamGame
from PIL import Image
img=sys.argv[1]; rec=bytes.fromhex(sys.argv[2]); frames=int(sys.argv[3]); tag=sys.argv[4]
def bf(k):
    d=bytearray(E.pblk(k))
    if E.MAPK.get(k)==2:
        o=1+0x971B-0x9056; d[o:o+7]=rec
    return bytes(d)
g=RamGame(open(img,'rb').read(), det_seed=5, blockfn=bf); m=g.m; rnd=random.Random(5)
C.boot(g); C.play(g,20,rnd); C.complete_and_next(g,1)
p1=0xAF52; ims=[]; ev={'P1 golpeado':0,'otros enemigos golpeados':0,'Jeff golpeado':0}
prev={}
for f in range(frames):
    m.release_all()
    if 'fight' in tag and f%6<3: m.key('RET'); m.key(rnd.choice(['LEFT','RIGHT','UP','DOWN']))
    g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96)
    for k,nm in ((0,'P1 golpeado'),(2,'Jeff golpeado'),(3,'otros enemigos golpeados'),(4,'otros enemigos golpeados')):
        a=p1+18*k; s=m.peek(a+9)
        if s==0x3D and prev.get(k)!=0x3D and m.peek(a): ev[nm]+=1
        prev[k]=s
    if f==700: m.poke(p1+36+17,3)
    if f%20==0 and f>=680:
        a=p1+36; print(f,'Jeff a%02X t%02X s%02X x%02X y%02X e%02X'%(m.peek(a),m.peek(a+15),m.peek(a+9),m.peek(a+3),m.peek(a+4),m.peek(a+17)),'P1 s%02X x%02X'%(m.peek(p1+9),m.peek(p1+3)),'967A=%d score=%02X%02X lives=%d'%(m.peek(0x967A),m.peek(0x5B01),m.peek(0x5B00),m.peek(0x5B09)))
    if f%15==0 and len(ims)<24:
        m.run(1); g.run_until([C.FRAME],100_000_000); m.screenshot('enem/tmp.png',1); ims.append(Image.open('enem/tmp.png').convert('RGB'))
    m.run(1)
print(ev)
W=Image.new('RGB',(256*6,192*4))
for i,im in enumerate(ims): W.paste(im,((i%6)*256,(i//6)*192))
W.save('enem/jt_%s.png'%tag)
