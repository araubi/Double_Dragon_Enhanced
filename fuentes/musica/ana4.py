import sys,numpy as np,collections
from ana2 import notes
path=sys.argv[1];P=float(sys.argv[2]);off=float(sys.argv[3])
ev=notes(path)
# residual per channel over time windows
for ch in range(8):
    ts=np.array([t for t,c,p in ev if c==ch],float)
    if len(ts)==0: continue
    ps=[p for t,c,p in ev if c==ch]
    res=(ts-off)/P; fr=res-np.round(res)
    print('ch%d n=%d pitch %d-%d frac hist'%(ch,len(ts),min(ps),max(ps)),np.histogram(fr,bins=8,range=(-0.5,0.5))[0])
# time-resolved
ts=np.array([t for t,c,p in ev],float); res=(ts-off)/P; fr=res-np.round(res)
for w in range(0,int(ts.max()/44100)+1,5):
    sel=(ts>=w*44100)&(ts<(w+5)*44100)
    if sel.sum(): print(w,'s', np.histogram(fr[sel],bins=8,range=(-0.5,0.5))[0])
