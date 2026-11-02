"""Lector mínimo de VGM: devuelve (muestra, tipo, registro, valor) de YM2151 y OKIM6295."""
import struct,sys,collections
def events(d):
    ver=struct.unpack_from('<I',d,8)[0]
    doff=0x34+struct.unpack_from('<I',d,0x34)[0] if ver>=0x150 else 0x40
    loopoff=0x1C+struct.unpack_from('<I',d,0x1C)[0]
    p=doff;t=0
    while p<len(d):
        c=d[p]
        if p==loopoff: yield (t,'loop',0,0)
        if c==0x54: yield (t,'opm',d[p+1],d[p+2]); p+=3
        elif c==0x61: t+=struct.unpack_from('<H',d,p+1)[0]; p+=3
        elif c==0x62: t+=735;p+=1
        elif c==0x63: t+=882;p+=1
        elif 0x70<=c<=0x7F: t+=(c&15)+1;p+=1
        elif c==0x66: yield (t,'end',0,0); return
        elif c==0xB8: yield (t,'oki',d[p+1],d[p+2]); p+=3
        elif c==0x67: n=struct.unpack_from('<I',d,p+3)[0]; p+=7+n
        elif 0x30<=c<=0x3F: p+=2
        elif 0x40<=c<=0x4E or 0x50<=c<=0x5F or 0xA0<=c<=0xBF: p+=3
        elif 0xC0<=c<=0xDF: p+=4
        elif 0xE0<=c<=0xFF: p+=5
        else: raise Exception('cmd %02x at %x'%(c,p))
