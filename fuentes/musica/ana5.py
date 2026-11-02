import sys,gzip,collections,numpy as np
import vgmparse as V
NOTEIDX={0:0,1:1,2:2,4:3,5:4,6:5,8:6,9:7,10:8,12:9,13:10,14:11}
def notes_full(path):
    d=gzip.decompress(open(path,'rb').read())
    reg=[0]*256;on={};out=collections.defaultdict(list);patches={}
    for t,k,r,v in V.events(d):
        if k!='opm':continue
        if r==8:
            ch=v&7
            if ch in on:
                s=on.pop(ch); out[ch].append((s[0],t,s[1],s[2]))
            if v&0x78:
                kc=reg[0x28+ch]
                p=12*((kc>>4)&7)+NOTEIDX.get(kc&15,0)+13
                patch=tuple(reg[a+ch+8*o] for a in (0x40,0x60,0x80,0xA0,0xC0,0xE0) for o in range(4) if a!=0x60)+(reg[0x20+ch]&0x3F,)
                pid=patches.setdefault(patch,len(patches))
                on[ch]=(t,p,pid)
        else: reg[r]=v
    return out
if __name__=='__main__':
  for path in sys.argv[1:]:
    print('==',path)
    N=notes_full(path)
    for ch in sorted(N):
        ns=N[ch]; ps=[n[2] for n in ns]; du=np.array([n[1]-n[0] for n in ns])/44100
        pc=collections.Counter(n[3] for n in ns)
        print(' ch%d n=%d pitch %d-%d mean %.1f dur med %.2fs patches %s'%(ch,len(ns),min(ps),max(ps),np.mean(ps),np.median(du),dict(pc.most_common(5))))
        if len(set(ps))<12: print('    pitches',collections.Counter(zip(ps,[n[3] for n in ns])).most_common(8))
