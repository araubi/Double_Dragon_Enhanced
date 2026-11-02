import coverage as C, equiv as E, random, sys
from ramgame import RamGame
from PIL import Image
which=sys.argv[1]; ms_t=int(sys.argv[2]); FR=int(sys.argv[3])
VARS={2:(0xC6BB,0x967C,0x9679),7:(0x96E8,0xC40E,0x96E5)}
POS,LIM,CNT=VARS[ms_t]
ORIGT=open('../dd/b19.bin','rb').read()[1:]
def bfo(k):
    d=bytearray(E.pblk(k))
    if E.MAPK.get(k)==7: o=0x97F0-0x9056; d[1+o:1+o+84]=ORIGT[o:o+84]
    return bytes(d)
img,bf=(('../dd/mem.bin',None) if which=='orig' else ('../build/patched_mem.bin',bfo if which=='newtab' else E.pblk))
g=RamGame(open(img,'rb').read(), det_seed=3, blockfn=bf); m=g.m; rnd=random.Random(3)
C.boot(g)
for ms in range(1,ms_t): C.play(g,20,rnd); C.complete_and_next(g,ms)
P1=[0xAE5D,0xAF52,0xAF2D,0xAF21,0xAF71,0xAEF4,0xAC63]; p1=P1[ms_t-1]
act={}; prev=[0]*8; log=[]; shots=0
for f in range(FR):
    m.release_all(); m.key('RIGHT')
    ph=f%160
    if 80<=ph<120: m.key('UP')
    elif ph>=120: m.key('DOWN')
    if f%7==0: m.key('RET')
    g.run_until([C.FRAME],100_000_000); m.poke(0x5B08,5); m.poke(p1+17,0x96); m.poke(p1+35,0x96)
    if m.peek(p1+18+9)<0x30: m.poke(p1+18+3,max(0,m.peek(p1+3)-3)); m.poke(p1+18+4,m.peek(p1+4))
    for k in (2,3,4):
        a=p1+18*k; on=m.peek(a)>=5 and m.peek(a+3)<0x20
        if on and not prev[k]:
            act[k]=f; t=m.peek(a+15); log.append((f,k,t,m.peek(a+17),m.peek(POS),m.peek(LIM),m.peek(CNT)))
            print('f%5d slot%d tipo %d energia %02X | scroll %02X limite %02X contador %d'%log[-1][0:1]+log[-1][1:] if False else 'f%5d slot%d tipo %d energia %02X | scroll %02X limite %02X contador %d'%log[-1],flush=True)
            if t in (0,2) and shots<6:
                m.run(1); g.run_until([C.FRAME],100_000_000); m.screenshot('enem/adv_%s_%d_%d.png'%(which,ms_t,shots),1); shots+=1
        prev[k]=on
        if on and f-act.get(k,f)>40 and (m.peek(a+15) not in (0,2)) and m.peek(a+9)!=0xFF:
            m.poke(a+9,0xFF); m.poke(a+8,0x10); m.poke(a+17,0)
    if f%500==0: m.screenshot('enem/advs_%s_%d_%05d.png'%(which,ms_t,f),1)
    if f%500==0: print('f%5d scroll %02X limite %02X contador %d P1x %02X'%(f,m.peek(POS),m.peek(LIM),m.peek(CNT),m.peek(p1+3)),flush=True)
    m.run(1)
