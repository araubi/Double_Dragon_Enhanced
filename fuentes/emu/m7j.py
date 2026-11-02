import coverage as C, equiv as E, random
from ramgame import RamGame
from PIL import Image
def bf(k):
    d=bytearray(E.pblk(k))
    if E.MAPK.get(k)==7:
        o=1+0x97F0-0x9056
        d[o:o+7]=bytes.fromhex('00005003200600'); d[o+7:o+14]=bytes.fromhex('02005A03fd0800')
    return bytes(d)
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=5, blockfn=bf); m=g.m; rnd=random.Random(5)
C.boot(g)
for ms in range(1,7): C.play(g,20,rnd); C.complete_and_next(g,ms)
p1=0xAC63; ims=[]
for f in range(300):
    m.release_all(); g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if f%30==0:
        print(f,' | '.join('k%d a%02X t%02X s%02X x%02X y%02X'%(k,m.peek(p1+18*k),m.peek(p1+18*k+15),m.peek(p1+18*k+9),m.peek(p1+18*k+3),m.peek(p1+18*k+4)) for k in (2,3)),'JFLAG',m.peek(0xE173))
        m.run(1); g.run_until([C.FRAME],100_000_000); m.screenshot('enem/tmp.png',1); ims.append(Image.open('enem/tmp.png').convert('RGB'))
    m.run(1)
W=Image.new('RGB',(256*5,192*2))
for i,im in enumerate(ims[:10]): W.paste(im,((i%5)*256,(i//5)*192))
W.save('enem/m7_jeff.png')
