import coverage as C, equiv as E, random
from ramgame import RamGame
from PIL import Image
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=5, blockfn=E.pblk); m=g.m; rnd=random.Random(5)
C.boot(g)
for ms in range(1,5): C.play(g,20,rnd); C.complete_and_next(g,ms)
p1=0xAF71; ims=[]
for f in range(900):
    m.release_all()
    if f%60<30: m.key('RIGHT')
    g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if m.peek(p1+18+9)<0x30: m.poke(p1+18+3,max(0,m.peek(p1+3)-3))
    if f%45==0:
        print(f,' | '.join('k%d a%02X t%02X s%02X x%02X y%02X'%(k,m.peek(p1+18*k),m.peek(p1+18*k+15),m.peek(p1+18*k+9),m.peek(p1+18*k+3),m.peek(p1+18*k+4)) for k in (2,3)))
        m.run(1); g.run_until([C.FRAME],100_000_000); m.screenshot('enem/tmp.png',1); ims.append(Image.open('enem/tmp.png').convert('RGB'))
    m.run(1)
W=Image.new('RGB',(256*5,192*4))
for i,im in enumerate(ims[:20]): W.paste(im,((i%5)*256,(i//5)*192))
W.save('enem/m4_jeff.png')
