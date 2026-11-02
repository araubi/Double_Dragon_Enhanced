import sys,numpy as np,collections
from ana5 import notes_full
from ana7 import SONGS
SONGS['01_Double_Dragon_Opening_Theme.vgz']=(4238.8,36640-8*4238.8)
MEL={'02':[0,1,2,3],'06':[1,2,3,4],'07':[0,1,2,3],'08':[0,1,2,3],'09':[0,1,2,3],'01':[0,2,3,4]}
for path,(P,off) in SONGS.items():
    N=notes_full(path); g={}
    for ch in MEL[path[:2]]:
        for s,e,p,_ in N[ch]:
            a=round((s-off)/P);b=max(a+1,round((e-off)/P))
            for t in range(a,b): g.setdefault(t,{})[ch]=p
    top=collections.Counter();snd=collections.Counter()
    for t,d in g.items():
        mx=max(d.values())
        for c,p in d.items():
            snd[c]+=1
            if p==mx: top[c]+=1
    print(path[:2],{c:'%.2f/%d'%(top[c]/snd[c],snd[c]) for c in sorted(snd)})
