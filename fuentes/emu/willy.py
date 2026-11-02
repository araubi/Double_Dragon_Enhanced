import coverage as C, equiv as E, random, sys
from ramgame import RamGame
from PIL import Image
def bf(k):
    d=bytearray(E.pblk(k))
    if E.MAPK.get(k)==7:
        o=1+0x97F0-0x9056
        d[o:o+7]=bytes.fromhex('02005A03200800')   # Willy first
        for r in range(12): d[o+7*r+6]=0
    return bytes(d)
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=5, blockfn=bf); m=g.m; rnd=random.Random(5)
C.boot(g)
for ms in range(1,7): C.play(g,20,rnd); C.complete_and_next(g,ms)
p1=m.peek(0x1C92)|m.peek(0x1C93)<<8; print('P1 %04X'%p1)
shots=[]
for f in range(700):
    m.release_all()
    if f%40<20: m.key('RIGHT')
    g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if f%10==0:
        line=[]
        for k in range(2,8):
            a=p1+18*k
            line.append('k%d a%02X t%02X s%02X x%02X y%02X e%02X'%(k,m.peek(a),m.peek(a+15),m.peek(a+9),m.peek(a+3),m.peek(a+4),m.peek(a+17)))
        print(f,' | '.join(line),'ptr %02X%02X n=%d'%(m.peek(0x96E4),m.peek(0x96E3),m.peek(0x96E5))) if 1 else print(f,' | '.join(line),'P1',bytes(m.peek(p1+i) for i in range(18)).hex(),'P2',bytes(m.peek(p1+18+i) for i in range(18)).hex(),'5B04',[m.peek(0x5B04+i) for i in range(8)],'96E5=%d'%m.peek(0x96E5),'C6BB=%02X'%m.peek(0xC6BB))
    if f%35==0: m.screenshot('enem/w_%04d.png'%f,1); shots.append(f)
    m.run(1)
ims=[Image.open('enem/w_%04d.png'%f) for f in shots[:20]]
W=Image.new('RGB',(256*5,192*4))
for i,im in enumerate(ims): W.paste(im,((i%5)*256,(i//5)*192))
W.save('enem/willy_strip.png')
