import sys,os,random; sys.path.insert(0,os.getcwd())
import romtest as R, coverage as C
from rommachine import machine
g=R.G(machine(open('../build/DoubleDragon_ASCII8.rom','rb').read(),'A')); m=g.m
R.boot(g)
for k in range(1,7): R.next_mission(g,k)
rnd=random.Random(1); last=-1
for it in range(900):
    if it%6==0:
        m.release_all(); m.key('RIGHT')
        if it>360: m.key(['UP','DOWN',None,'UP'][(it//120)%4] or 'RIGHT')
        elif (it//300)%2: m.key('UP')
        if rnd.random()<0.5: m.key('SPACE')
    assert g.run_until([C.FRAME],80_000_000)==C.FRAME
    m.poke(0x5B08,5); p1=m.peekw(0x1C92); m.poke(p1+17,0x96)
    for k in range(2,6):
        e=p1+18*k
        if m.peek(e) and m.peek(e+15) not in (0,2) and m.peek(e+9)<0xFE and m.peek(e+3)<0x1F: m.poke(e+9,0xFF); m.poke(e+8,0x10); m.poke(e+17,0)
    sc=m.peek(0xC40E)
    if sc!=last:
        last=sc; m.screenshot('shots/s%02X.png'%sc,1)
        print(it,'%02X'%sc,'P1 x%02X y%02X'%(m.peek(p1+3),m.peek(p1+4)))
    for k in range(2,6):
        e=p1+18*k
        if m.peek(e) and m.peek(e+15)==2 and it<380 and it%3==0:
            print('  willy',it,'sc %02X'%sc,' '.join('%02X'%m.peek(e+i) for i in range(18)))
            m.screenshot('shots/w%04d.png'%it,1)
    if it%40==39: print(it,'sc %02X'%sc,'P1 %02X %02X'%(m.peek(p1+3),m.peek(p1+4)),'pend',m.peek(0x96E5),[' '.join('%02X'%m.peek(p1+18*k+i) for i in (0,3,4,9,15,17)) for k in range(2,6)],[m.peek(0x96E0+i) for i in range(6)])
    m.run(1)
