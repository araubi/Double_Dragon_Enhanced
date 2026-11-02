import sys,numpy as np
from ana2 import notes
for path in sys.argv[1:]:
    ev=notes(path); sr=44100
    T=np.array([e[0] for e in ev]); last=T.max()
    # onset strength per channel in 20ms bins; autocorrelation over time with pitch match
    B=441*2
    keys=set((int(t//B),ch,p) for t,ch,p in ev)
    keys2=set()
    for k in keys:
        for dt in (-1,0,1): keys2.add((k[0]+dt,k[1],k[2]))
    nb=int(last//B)
    out=[]
    for L in range(int(5*sr/B),nb//2+10):
        tot=hit=0
        for (b,ch,p) in keys:
            if b+L<=nb:
                tot+=1; hit+=(b+L,ch,p) in keys2
        if tot>50: out.append((hit/tot,L*B/sr,tot))
    out.sort(reverse=True)
    print(path,'dur %.1f'%(last/sr),[('%.3f'%a,'%.2fs'%b,c) for a,b,c in out[:5]])
