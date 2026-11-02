import sys,gzip,collections,numpy as np
import vgmparse as V
NOTEIDX={0:0,1:1,2:2,4:3,5:4,6:5,8:6,9:7,10:8,12:9,13:10,14:11}
CAR={0:[3],1:[3],2:[3],3:[3],4:[1,3],5:[1,2,3],6:[1,2,3],7:[0,1,2,3]}
def info(path):
    d=gzip.decompress(open(path,'rb').read())
    reg=[0]*256;out=collections.defaultdict(list)
    for t,k,r,v in V.events(d):
        if k!='opm':continue
        if r==8 and v&0x78:
            ch=v&7;kc=reg[0x28+ch]
            p=12*((kc>>4)&7)+NOTEIDX.get(kc&15,0)+13
            con=reg[0x20+ch]&7
            # operator slot order M1,M2,C1,C2 -> reg offsets 0,8,16,24 are M1,C1,M2,C2
            offs=[0,16,8,24]
            tl=min(reg[0x60+ch+offs[o]]&0x7F for o in CAR[con])
            out[ch].append((t,p,tl))
        elif r!=8: reg[r]=v
    return out
for path in sys.argv[1:]:
    print('==',path)
    N=info(path)
    for ch in sorted(N):
        tl=[x[2] for x in N[ch]]
        print(' ch%d carrierTL med %d'%(ch,np.median(tl)),end='')
        S={(round(t/441),p%12) for t,p,_ in N[ch]}
        ov=[]
        for c2 in sorted(N):
            if c2==ch: continue
            S2={(round(t/441),p%12) for t,p,_ in N[c2]}
            S2|={(a+1,b) for a,b in S2}|{(a-1,b) for a,b in S2}
            f=len(S&S2)/len(S)
            if f>0.3: ov.append('ch%d:%.2f'%(c2,f))
        print(' overlaps',ov)
