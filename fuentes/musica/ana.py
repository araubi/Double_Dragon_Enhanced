import sys,gzip,collections,struct
import vgmparse as V
NOTEIDX={0:0,1:1,2:2,4:3,5:4,6:5,8:6,9:7,10:8,12:9,13:10,14:11}
for path in sys.argv[1:]:
    d=gzip.decompress(open(path,'rb').read())
    tot=struct.unpack_from('<I',d,0x18)[0]; lp=struct.unpack_from('<I',d,0x20)[0]
    reg=[0]*256;on=collections.Counter();starts=collections.defaultdict(list);loopt=None;oki=0
    for t,k,r,v in V.events(d):
        if k=='loop': loopt=t
        if k=='oki': oki+=1
        if k=='opm' and r==8 and v&0x78: starts[v&7].append(t)
        if k=='end': end=t
    print(path,'total %.1fs loopsamples %d (%.1fs) loopstart %s end %d oki %d'%(tot/44100,lp,lp/44100,loopt,end,oki))
    allst=sorted(set(x for c in starts for x in starts[c]))
    import numpy as np
    dif=np.diff(allst); dif=dif[dif>200]
    print('  ch counts',{c:len(starts[c]) for c in sorted(starts)},' first',allst[0],' common diffs',collections.Counter((dif/10).round().astype(int)*10).most_common(6))
