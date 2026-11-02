import sys,gzip,collections,numpy as np
import vgmparse as V
NOTEIDX={0:0,1:1,2:2,4:3,5:4,6:5,8:6,9:7,10:8,12:9,13:10,14:11}
def notes(path):
    d=gzip.decompress(open(path,'rb').read())
    reg=[0]*256;ev=[]
    for t,k,r,v in V.events(d):
        if k!='opm':continue
        if r==8:
            if v&0x78:
                ch=v&7;kc=reg[0x28+ch]
                ev.append((t,ch,12*((kc>>4)&7)+NOTEIDX.get(kc&15,0)+13))
        else: reg[r]=v
    return ev
def fit(ts,P0):
    best=None
    for P in np.arange(P0*0.97,P0*1.03,P0*0.0002):
        ph=(ts/P)%1; ang=np.angle(np.exp(2j*np.pi*ph).mean()); r=abs(np.exp(2j*np.pi*ph).mean())
        if best is None or r>best[0]: best=(r,P,(ang/(2*np.pi))%1*P)
    return best
if __name__=="__main__":
 for path,P0 in zip(sys.argv[1::2],sys.argv[2::2]):
     ev=notes(path); ts=np.array([e[0] for e in ev],float)
     r,P,off=fit(ts,float(P0))
     q=[(int(round((t-off)/P)),ch,p) for t,ch,p in ev]
     err=np.abs(ts-off-np.round((ts-off)/P)*P).max()
     S=set(q); last=max(x[0] for x in q)
     # find repetition: smallest L>=16 such that from some start s, events t>=s and t+L<=last are in S
     res=[]
     for L in range(16,last):
         bad=[t for t,ch,p in q if t+L<=last and (t+L,ch,p) not in S]
         s=max(bad)+1 if bad else 0
         if last-L-s>=L*0.9: res.append((L,s)); break
     print(path,'P=%.2f off=%.0f r=%.3f maxerr=%.0f last=%d'%(P,off,r,err,last),res)
 