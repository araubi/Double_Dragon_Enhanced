"""CAS end-to-end: load via the tape loader, play the 7 loads, check page-0 code and Abobo hook."""
import random, sys
import romtest as R
from castest import CasMachine
from rommachine import machine
REG=((0x00B0,0x0100),(0x0482,0x0556),(0x1C92,0x1D00),(0x0654,0x0677),(0x0BDC,0x0C61),(0x0CAB,0x0CDF),(0x1D40,0x1DC0),(0xE173,0xE200),(0xED8D,0xEE48))
def check(name,g,ref):
    m=g.m; rnd=random.Random(5); R.boot(g)
    bad=[hex(a) for s,e in REG for a in range(s,e) if m.peek(a)!=ref[a]]
    out=[]
    for ms in range(1,8):
        R.play(g,40,rnd)
        p1=m.peek(0x1C92)|m.peek(0x1C93)<<8; hit=m.peek(0x1C94)|m.peek(0x1C95)<<8
        r=g.run_until([0x04A8],30_000_000)          # ABOCHK runs every frame
        out.append('m%d P1=%04X HIT=%04X dif=%d abochk=%s'%(ms,p1,hit,R.ram_ok(m,ms) if ms>1 else -1,'ok' if r==0x04A8 else 'NO'))
        if ms<7: R.next_mission(g,ms)
    print(name,'page-0 bytes differing:',bad); print('  '+'\n  '.join(out))
ref=open('../build/cas_mem.bin','rb').read()
check('CAS',CasMachine(open('../build/DoubleDragon_optimizado.cas','rb').read()),ref)
check('ROM-A',R.G(machine(open('../build/DoubleDragon_ASCII8.rom','rb').read(),'A')),open('../build/patched_mem.bin','rb').read())
