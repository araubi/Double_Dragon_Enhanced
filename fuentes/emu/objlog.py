import sys,os,random
sys.path.insert(0,os.getcwd())
import romtest, coverage as C
from rommachine import machine
rom=open(sys.argv[1],'rb').read()
m=machine(rom,'A'); m.det_r(True,1); g=romtest.G(m); rnd=random.Random(5)
assert g.run_until([0x0D03],600_000_000)==0x0D03
m.key('SPACE'); m.run(3_000_000); m.key('SPACE',False)
assert g.run_until([C.TITLE[1]])==C.TITLE[1]; m.run(3_000_000)
m.key('SPACE'); assert g.run_until([C.FRAME])==C.FRAME; m.key('SPACE',False)
p1=m.peekw(0x1C92); prev=None
for f in range(int(sys.argv[2])):
    if f%4==0:
        m.release_all()
        for k in rnd.choice([('RIGHT',),('RIGHT',),('RIGHT',),('SPACE','RIGHT'),('UP',),('DOWN',),('RIGHT','UP'),('RIGHT','DOWN')]): m.key(k)
    assert g.run_until([C.FRAME])==C.FRAME; m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    st=[]
    for k in range(5,8):
        b=p1+18*k; st.append(' '.join('%02X'%m.peek(b+i) for i in range(18)))
    act=' | '.join('%d:%02X/%02X'%(k,m.peek(p1+18*k+15),m.peek(p1+18*k+7)) for k in range(5) if m.peek(p1+18*k))
    key=(tuple(x[:2] for x in st),act)
    if key!=prev: print(f,act); [print('    obj',x) for x in st]; prev=key
    for k in range(2,5):
        b=p1+18*k
        if m.peek(b) and f%60==59 and m.peek(b+9)<0x30 and m.peek(b+15)&15!=2: m.poke(b+9,0xFF); m.poke(b+8,0x10); m.poke(b+17,0)
    m.run(1)
