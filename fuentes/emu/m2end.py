import coverage as C, equiv as E, random
from ramgame import RamGame
from PIL import Image
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=5, blockfn=E.pblk); m=g.m; rnd=random.Random(5)
C.boot(g); C.play(g,20,rnd); C.complete_and_next(g,1)
p1=0xAF52
for f in range(5): g.run_until([C.FRAME],100_000_000); m.run(1)
m.poke(0x9677,0x53); m.poke(0x9678,0x97); m.poke(0x9679,8)
for k in (2,3,4):
    a=p1+18*k; m.poke(a+9,0xFF); m.poke(a+8,0x10); m.poke(a+17,0)
ims=[]
for f in range(400):
    m.release_all()
    if f==10: m.poke(0xB0FA,3)
    g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if f%40==0:
        print(f,' | '.join('k%d a%02X t%02X s%02X x%02X y%02X e%02X'%(k,m.peek(p1+18*k),m.peek(p1+18*k+15),m.peek(p1+18*k+9),m.peek(p1+18*k+3),m.peek(p1+18*k+4),m.peek(p1+18*k+17)) for k in (2,3,4)))
        m.run(1); g.run_until([C.FRAME],100_000_000); m.screenshot('enem/tmp.png',1); ims.append(Image.open('enem/tmp.png').convert('RGB'))
    m.run(1)
W=Image.new('RGB',(256*5,192*2))
for i,im in enumerate(ims[:10]): W.paste(im,((i%5)*256,(i//5)*192))
W.save('enem/m2_final.png')
