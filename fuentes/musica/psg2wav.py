# Uso: python3 psg2wav.py cap.pkl salida.wav cuadro_inicio cuadro_fin [cuadros_por_segundo, 50 por defecto]
"""Render PSG (AY-3-8910) a WAV a partir de registros por cuadro (numpy)."""
import sys,pickle,wave,numpy as np
frames,marks=pickle.load(open(sys.argv[1],'rb')); out=sys.argv[2]
a,b=int(sys.argv[3]),int(sys.argv[4]); fps=float(sys.argv[5]) if len(sys.argv)>5 else 50.0
VOL=np.array([0,0.0106,0.0150,0.0222,0.0320,0.0466,0.0665,0.1039,0.1237,0.1986,0.2803,0.3548,0.4702,0.5948,0.7973,1.0])
SR=44100; CLK=1789772.5
spf=SR/fps; ph=np.zeros(3); nph=0.0; lfsr=1; res=[]
rng=np.random.default_rng(1)
for fi in range(a,b):
    r=frames[fi]; n=int(round((fi-a+1)*spf))-int(round((fi-a)*spf))
    mix=r[7]; v=np.zeros(n)
    nper=(r[6]&31) or 1
    # ruido: muestra y retén a la frecuencia del ruido
    nf=CLK/(16*nper)/2
    idx=np.floor((nph+np.arange(n)*nf/SR)).astype(int); nph+=n*nf/SR
    noise=rng.integers(0,2,idx.max()-idx.min()+1)[idx-idx.min()]
    for c in range(3):
        per=(r[2*c]|(r[2*c+1]&15)<<8) or 1
        f=CLK/(16*per)
        t=(ph[c]+np.arange(n)*f/SR); ph[c]=(ph[c]+n*f/SR)%1
        sq=(t%1)<0.5
        ton=sq if not (mix>>c)&1 else np.ones(n,bool)
        non=noise.astype(bool) if not (mix>>(c+3))&1 else np.ones(n,bool)
        v+=VOL[r[8+c]&15]*(ton&non)
    res.append(v)
v=np.concatenate(res)/3
v=v-np.convolve(v,np.ones(441)/441,'same')   # quitar continua
pcm=(np.clip(v*1.6,-1,1)*30000).astype('<i2')
w=wave.open(out,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print(len(pcm)/SR)
