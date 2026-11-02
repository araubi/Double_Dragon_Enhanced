"""Músicas de las misiones: VGM de la recreativa (YM2151) -> arreglo a 3 voces PSG + batería.
Uso: python3 arreglos.py [salida_dir]   (por defecto ../build; escribe mus_<id>.inc)
Cada VGM trae la introducción y una vuelta del bucle (los reproductores de VGM la repiten);
el arreglo se corta en el punto de bucle del VGM (o en la repetición detectada a mano).
Voces: A melodía (canales por prioridad), B bajo, C segunda voz con la batería encima.
Música: "Double Dragon" (Technos Japan, 1987), compuesta por Kazunaka Yamane."""
import sys,os,gzip,struct,collections
import numpy as np
import vgmparse as V
NOTEIDX={0:0,1:1,2:2,4:3,5:4,6:5,8:6,9:7,10:8,12:9,13:10,14:11}
HERE=os.path.dirname(os.path.abspath(__file__))
# id: fichero, semicorchea aprox., voz A, voz B, voz C, canales de batería, notas de bombo, (inicio bucle, fin) en semicorcheas o None
# [, {canal: (desde, hasta)} notas que no se usan [, opciones]]
# opciones: sub = pasos de reproductor por semicorchea (para barridos rápidos), instc =
# instrumentos de la voz C por canal, wah = envolvente "wah" en melodía y voz C (WAH EQU 1)
SONGS={
 '02':('02_Slums_Arrival_of_the_Black_Warriors.vgz',4238,[1,3,2],[4],[2,3],[5,6],{45},'vgm'),
 '06':('06_Industrial_Area_Riot.vgz',5299,[3,4,1],[0],[1,2],[5,6],{43,41},'vgm'),
 '07':('07_Woods.vgz',5828,[0,1],[4],[1,2,3],[5,6],set(),'vgm'),
 '08':('08_Enemy_Headquarters_Old_Nemesis_Willy.vgz',4238,[0,2],[4],[1,3,2],[5,6],{45},'vgm'),
 '09':('09_Reunion_with_Marian_Ending_Theme.vgz',6888,[0,2],[4],[3,1],[],set(),(16,208)),
 '04':('04_Mission_Complete.vgz',3355,[3,2],[4],[1,0],[],set(),None),
 # 03: 64 pasos de entrada (ostinato, sirena en el canal 0, cuatro golpes) y 128 de riff; el
 # canal 0 dobla el bajo en el riff, así que la voz C toma ahí la armonía del canal 2. Como en
 # la recreativa, el bucle vuelve a la entrada con la sirena (antes solo repetía el riff)
 '03':('03_The_Entrance_of_Abobo_the_Giant.vgz',5826,[1],[3,2],[0,4,2],[5],{36},(0,192),{0:(64,999)},
       dict(sub=6,instc=[3,2,2],wah=1)),   # la sirena (canal 0) va a 1/6 de semicorchea
}
def load(path):
    d=gzip.decompress(open(path,'rb').read())
    tot=struct.unpack_from('<I',d,0x18)[0]; lp=struct.unpack_from('<I',d,0x20)[0]
    reg=[0]*256; on={}; N=collections.defaultdict(list)
    for t,k,r,v in V.events(d):
        if k!='opm': continue
        if r==8:
            ch=v&7
            if ch in on:
                s=on.pop(ch); N[ch].append((s[0],t,s[1]))
            if v&0x78:
                kc=reg[0x28+ch]
                on[ch]=(t,12*((kc>>4)&7)+NOTEIDX.get(kc&15,0)+13)
        else: reg[r]=v
    for ch,s in on.items(): N[ch].append((s[0],tot,s[1]))
    return N,tot,lp
def fitgrid(N,P0):
    ts=np.array(sorted(s for ch in N for s,e,p in N[ch]),float)
    best=None
    for P in np.arange(P0*0.98,P0*1.02,P0*0.0001):
        z=np.exp(2j*np.pi*ts/P).mean()
        if best is None or abs(z)>best[0]: best=(abs(z),P,(np.angle(z)/(2*np.pi))%1*P)
    _,P,off=best
    for it in range(5):
        k=np.round((ts-off)/P); P,off=np.linalg.lstsq(np.vstack([k,np.ones_like(k)]).T,ts,rcond=None)[0]
    return P,off
def arrange(sid):
    fn,P0,VA_,VB_,VC_,DR,KICK,loop=SONGS[sid][:8]
    cut=SONGS[sid][8] if len(SONGS[sid])>8 else {}
    opt=SONGS[sid][9] if len(SONGS[sid])>9 else {}
    sub=opt.get('sub',1)
    cut={ch:(a*sub,b*sub) for ch,(a,b) in cut.items()}
    N,tot,lp=load(os.path.join(HERE,fn))
    P,off=fitgrid(N,P0)
    P/=sub
    q=lambda x: int(round((x-off)/P))
    Q={ch:sorted((q(s),max(q(s)+1,q(e)),p) for s,e,p in N[ch]) for ch in N}
    for ch,(a,b) in cut.items(): Q[ch]=[n for n in Q[ch] if not a<=n[0]<b]
    t0=min(n[0] for ch in Q for n in Q[ch])
    if loop=='vgm': L0,L1=int(round((tot-lp-off)/P)),int(round((tot-off)/P))
    elif loop is None: L0=L1=max(n[1] for ch in Q for n in Q[ch])+1
    else: L0,L1=loop[0]*sub,loop[1]*sub
    # rejilla por canal: t -> (nota, empieza)
    G={}
    for ch,ns in Q.items():
        g={}
        for i,(ts,te,p) in enumerate(ns):
            nx=ns[i+1][0] if i+1<len(ns) else L1
            for t in range(ts,min(nx,te+1,L1)): g[t]=(p,t==ts)
        G[ch]=g
    def voice(prio,inst,excl=None):
        v={}
        for t in range(t0,L1):
            for i,ch in enumerate(prio):
                if excl and excl.get(t,(0,0,-1))[2]==ch: continue
                if t in G.get(ch,{}):
                    p,st=G[ch][t]; prev=v.get(t-1)
                    st=st or prev is None or prev[2]!=ch or prev[0]!=p
                    v[t]=(p,inst[i] if isinstance(inst,list) else inst,ch,st); break
        return v
    VA=voice(VA_,[0]+[3]*(len(VA_)-1)); VB=voice(VB_,1); VC=voice(VC_,opt.get('instc',2),VA)
    D={}
    for ch in DR:
        for ts,te,p in Q.get(ch,[]):
            if not (t0<=ts<L1): continue
            if p>=80: k=(3,0)
            elif p==38: k=(2,0)
            elif p in KICK: k=(1,0)
            elif p==72: k=(4,0)
            else: k=(5,p+12)
            old=D.get(ts)
            if old is None or old[0]==3: D[ts]=k        # el charles cede ante otro golpe
    def enc(v,drums=False):
        out=[];lpos=None;t=t0
        while t<L1:
            if t==L0: lpos=len(out)
            n=v.get(t); d=1
            if drums:
                while t+d<L1 and t+d not in v and t+d!=L0 and d<63: d+=1
                k,p=n if n else (0,0)
                out+=[k if k!=5 else 0x40|(p-24), d]
            elif n is None:
                while t+d<L1 and t+d not in v and t+d!=L0 and d<63: d+=1
                out+=[0x60,d]
            else:
                p,inst,ch,st=n
                while t+d<L1 and t+d!=L0 and d<63:
                    m=v.get(t+d)
                    if m is None or m[3] or m[0]!=p: break
                    d+=1
                assert 24<=p<120,p
                out+=[p-24,d|(inst<<6)]
            t+=d
        if lpos is None:            # sin bucle: silencio eterno al final
            lpos=len(out); out+=[0x60 if not drums else 0,63]
        return out+[0xFF],lpos
    streams=[enc(VA),enc(VB),enc(VC),enc(D,True)]
    return streams,P,(t0,L0,L1),opt
if __name__=='__main__':
    od=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,'..','build')
    for sid in SONGS:
        streams,P,(t0,L0,L1),opt=arrange(sid)
        L=['; generado por arreglos.py desde "%s" (recreativa, YM2151)'%SONGS[sid][0],
           'MUS_TICK EQU %d   ; paso en 1/100000 s'%round(P/44100*1e5)]
        if opt.get('wah'): L.append('WAH EQU 1   ; envolvente "wah" (mus_player.asm)')
        for name,(s,lp) in zip(('MUS_A','MUS_B','MUS_C','MUS_D'),streams):
            L.append('%s_LOOP EQU %s+%d'%(name,name,lp)); L.append(name+':')
            for i in range(0,len(s),16): L.append('            db '+','.join('%d'%b for b in s[i:i+16]))
        open(os.path.join(od,'mus_%s.inc'%sid),'w').write('\n'.join(L)+'\n')
        print(sid,'P=%.1f (%.4f s) ticks %d..%d bucle %d'%(P,P/44100,t0,L1,L0),[len(s) for s,l in streams],sum(len(s) for s,l in streams))
