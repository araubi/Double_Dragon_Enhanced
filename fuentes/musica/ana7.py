import sys,numpy as np,collections
from ana5 import notes_full
SONGS={'02_Slums_Arrival_of_the_Black_Warriors.vgz':(4238.46,829),'06_Industrial_Area_Riot.vgz':(5299.0,668),'07_Woods.vgz':(5828.15,533),
'08_Enemy_Headquarters_Old_Nemesis_Willy.vgz':(4238.46,292),'09_Reunion_with_Marian_Ending_Theme.vgz':(6888.26,607)}
for path,(P,off) in SONGS.items():
    N=notes_full(path); print('==',path)
    for ch in sorted(N):
        q=[(round((s-off)/P),round((e-off)/P),p) for s,e,p,_ in N[ch]]
        last=max(x[1] for x in q)
        bars=collections.defaultdict(list)
        for s,e,p in q: bars[s//16].append((s%16,p))
        keys=[tuple(bars[b]) for b in range(last//16+1)]
        rep=sum(1 for i in range(1,len(keys)) if keys[i] and keys[i]==keys[i-1])/max(1,sum(1 for k in keys if k))
        cov=len(set(t for s,e,p in q for t in range(s,max(s+1,e))))/last
        print(' ch%d n=%d cov %.2f barrep %.2f distinct %d'%(ch,len(q),cov,rep,len(set(p for _,_,p in q))))
