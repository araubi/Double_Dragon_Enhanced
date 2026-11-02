import random, sys
from ramgame import RamGame
def start(img, seed=1):
    g=RamGame(img, det_seed=seed); m=g.m
    g.run_until([0x0D03]); m.key('SPACE'); g.run_until([0x919F]); m.key('SPACE',False)
    m.run(2_000_000); m.key('RET'); g.run_until([0x90F4]); m.key('RET',False)
    return g
def profile(g, iters=200, marks=((0xE612,'blit'),(0x06C2,'pat'),(0x06C5,'hud'),(0x06C8,'end'))):
    m=g.m; acc={}; tot0=m.cyc
    rnd=random.Random(7)
    for it in range(iters):
        # random-ish inputs keyed to loop iteration
        if it%10==0:
            m.release_all(); 
            for k in rnd.sample(['LEFT','RIGHT','UP','DOWN','RET','RET'],2): m.key(k)
        pc=g.run_until([0x90F4]+[a for a,_ in marks])
        stamps={}
        while pc!=0x90F4:
            stamps[pc]=m.cyc; pc=g.run_until([0x90F4]+[a for a,_ in marks])
        ks=[a for a,_ in marks]
        if all(k in stamps for k in ks):
            for (a,n),(b,_) in zip(marks,marks[1:]):
                acc[n]=acc.get(n,0)+stamps[b]-stamps[a]
    tot=m.cyc-tot0
    print('T/iter %.0f  fps %.2f'%(tot/iters, 3579545/(tot/iters)))
    for k,v in acc.items(): print('  %-5s %.0f T (%.0f%%)'%(k,v/iters,100*v/tot))
    return tot/iters
if __name__=='__main__':
    g=start(open('../dd/mem.bin','rb').read())
    profile(g)
