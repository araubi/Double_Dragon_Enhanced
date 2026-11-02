"""Música de presentación: VGM de la recreativa (YM2151) -> arreglo a 3 voces PSG.
Uso: python3 vgm2psg.py ["01 Double Dragon Opening Theme.vgz"] [../build/mus_data.inc]
Rejilla: semicorchea = 4238,8 muestras (0,0961 s); entrada de 8 semicorcheas y bucle de 512.
Voces: A melodía (canal 0 del YM, con el eco del canal 2 en los huecos), B bajo (canal 1),
C acompañamiento (canal 4, o el 3) con la batería (canales 5 y 6) mezclada encima."""
import sys,gzip,os,collections
import vgmparse as V
NOTEIDX={0:0,1:1,2:2,4:3,5:4,6:5,8:6,9:7,10:8,12:9,13:10,14:11}
CAR={0:[3],1:[3],2:[3],3:[3],4:[2,3],5:[1,2,3],6:[1,2,3],7:[0,1,2,3]}
P=4238.8;T0=36640
def load_notes(path):
    d=open(path,'rb').read()
    if d[:2]==b'\x1f\x8b': d=gzip.decompress(d)
    reg=[0]*256; on={}; notes=collections.defaultdict(list)
    def pitch(ch):
        kc=reg[0x28+ch]; kf=reg[0x30+ch]>>2
        return 12*((kc>>4)&7)+NOTEIDX.get(kc&15,0)+13+kf/64
    for t,k,r,v in V.events(d):
        if k!='opm': continue
        if r==8:
            ch=v&7
            if ch in on:
                s=on.pop(ch); notes[ch].append((s[0],t,s[1]))
            if v&0x78: on[ch]=(t,pitch(ch))
        else: reg[r]=v
    Q={}
    for ch in notes:
        for s,e,p in notes[ch]:
            ts=round((s-T0)/P); te=max(ts+1,round((e-T0)/P))
            Q.setdefault(ch,[]).append((ts,te,p,0))
    return Q
ARGS=sys.argv[1:]
Q=load_notes(ARGS[0] if ARGS else os.path.join(os.path.dirname(os.path.abspath(__file__)),'01 Double Dragon Opening Theme.vgz'))
T_IN,T_LOOP=-8,512
REL={0:2,1:1,2:1,3:1,4:2}
def tracks(ch):
    ns=sorted(Q[ch]); out=[]
    for i,(ts,te,p,v) in enumerate(ns):
        nx=ns[i+1][0] if i+1<len(ns) else T_LOOP
        end=min(nx,te+REL[ch],T_LOOP)
        if ts<0 and end>0: end=0
        out.append((ts,end,round(p)))
    return out
def grid(ch):
    g={}
    for ts,te,p in tracks(ch):
        for t in range(ts,te): g[t]=(p,t==ts)
    return g
G={ch:grid(ch) for ch in range(5)}
# instruments: 0 lead, 1 bass, 2 harmony, 3 echo (softer lead)
def voice(prio):
    v={}
    for t in range(T_IN,T_LOOP):
        for ch,inst in prio:
            if t in G[ch]:
                p,st=G[ch][t]
                prev=v.get(t-1)
                st=st or prev is None or prev[2]!=ch or prev[0]!=p
                v[t]=(p,inst,ch,st); break
    return v
VA=voice([(0,0),(2,3)])
VB=voice([(1,1)])
VC=voice([(4,2),(3,2)])
# drums from ch5/ch6: 1 kick, 2 snare, 3 hihat, 4 tom (with pitch)
D={}
for ts,te,p,v in Q[6]: D[ts]=(1,0)
for ts,te,p,v in Q[5]:
    p=round(p)
    if p>=100: D.setdefault(ts,(3,0))
    elif p==38: D[ts]=(2,0)
    else: D[ts]=(4,p+12)   # timbales una octava más arriba: en el PSG se oyen mejor
# ---- encode
def enc_voice(v):
    out=[];loop=None;t=T_IN
    while t<T_LOOP:
        if t==0: loop=len(out)
        n=v.get(t)
        if n is None:
            d=1
            while t+d<T_LOOP and t+d not in v and t+d!=0 and d<63: d+=1
            out+=[0x60,d]
        else:
            p,inst,ch,st=n; d=1
            while t+d<T_LOOP and t+d!=0 and d<63:
                m=v.get(t+d)
                if m is None or m[3] or m[0]!=p: break
                d+=1
            out+=[p-24, d|(inst<<6)]
        t+=d
    return out+[0xFF],loop
def enc_drums():
    out=[];loop=None;t=T_IN
    ev=sorted(D)
    while t<T_LOOP:
        if t==0: loop=len(out)
        if t in D:
            k,p=D[t]
        else: k,p=0,0
        d=1
        while t+d<T_LOOP and t+d not in D and t+d!=0 and d<63: d+=1
        out+=[(k if k!=4 else 0x40|(p-24)) ,d]
        t+=d
    return out+[0xFF],loop
if __name__=='__main__':
    streams=[enc_voice(VA),enc_voice(VB),enc_voice(VC),enc_drums()]
    L=['; generado por arrange.py desde "01 Double Dragon Opening Theme.vgz" (recreativa, YM2151)']
    for name,(s,lp) in zip(('MUS_A','MUS_B','MUS_C','MUS_D'),streams):
        L.append('%s_LOOP EQU %s+%d'%(name,name,lp))
        L.append(name+':')
        for i in range(0,len(s),16): L.append('            db '+','.join('%d'%b for b in s[i:i+16]))
    open(ARGS[1] if len(ARGS)>1 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','build','mus_data.inc'),'w').write('\n'.join(L)+'\n')
    print([len(s) for s,l in streams], sum(len(s) for s,l in streams))
