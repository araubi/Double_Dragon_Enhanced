"""PSG (AY-3-8910, MSX 1.7897725 MHz) render of one channel driven per 1/60 s frame."""
import numpy as np, wave
CLK=1789772.5
VOL=[0,0.0106,0.0150,0.0222,0.0320,0.0466,0.0665,0.1039,0.1237,0.1986,0.2803,0.3548,0.4702,0.6030,0.7530,1.0]
def render(steps, sr=44100, fps=60):
    """steps: list of (vol, tp or 0, np or 0)"""
    out=[]; tcnt=0.0; tstate=1; ncnt=0.0; lfsr=1; nout=1
    tick=CLK/8/sr   # PSG internal tone counter clocks per sample (clk/8, toggles every TP)
    for vol,tp,npd in steps:
        n=int(sr/fps); buf=np.zeros(n)
        for i in range(n):
            if tp:
                tcnt+=tick
                while tcnt>=tp: tcnt-=tp; tstate^=1
            if npd:
                ncnt+=tick
                while ncnt>=2*npd:
                    ncnt-=2*npd
                    bit=(lfsr^(lfsr>>3))&1; lfsr=(lfsr>>1)|(bit<<16); nout=lfsr&1
            t=tstate if tp else 1; z=nout if npd else 1
            buf[i]=VOL[vol]*(t&z) if (tp or npd) else 0
        out.append(buf)
    a=np.concatenate(out) if out else np.zeros(1)
    return a-np.convolve(a,np.ones(64)/64,'same')   # quitar continua
def save(path,a,sr=44100):
    a=np.clip(a*0.7,-1,1); w=wave.open(path,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((a*32767).astype(np.int16).tobytes()); w.close()
