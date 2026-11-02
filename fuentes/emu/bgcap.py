import sys; sys.path.insert(0,'.')
import random, numpy as np, pickle
from PIL import Image
import coverage as C, equiv as E, mockscale as MS
from ramgame import RamGame
g=RamGame(open('../build/patched_mem.bin','rb').read(), det_seed=5, blockfn=E.pblk); m=g.m; rnd=random.Random(5)
C.boot(g); out={}
for ms in range(1,8):
    C.play(g,30,rnd)
    img,figs=MS.capture(g,ms)
    Image.fromarray(img).save('shots/bg%d.png'%ms)
    m.screenshot('shots/sh%d.png'%ms,1)
    if ms<7: C.complete_and_next(g,ms)
