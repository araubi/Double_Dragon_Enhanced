"""Build the optimised CAS (same block structure as the original tape)."""
import subprocess, os, sys, functools
D=os.path.dirname(os.path.abspath(__file__)); DD=os.path.join(D,'..','dd')
SJ=os.environ.get('SJASMPLUS','sjasmplus')
def sj(src):
    r=subprocess.run([SJ,'--nologo','--msg=war','--lst='+src.replace('.asm','.lst'),'--sym='+src.replace('.asm','.sym'),src],cwd=D,capture_output=True,text=True)
    if r.returncode or r.stdout.strip() or r.stderr.strip(): print(r.stdout[-3000:],r.stderr[-3000:])
    if r.returncode: sys.exit(1)
subprocess.run([sys.executable,'build_ram.py'],cwd=D,check=True,capture_output=True)
open(os.path.join(D,'dd_cas.asm'),'w').write('''            DEVICE NOSLOT64K
            ORG 0
            INCBIN "original_mem.bin"
            INCLUDE "dd_cleanup.asm"
            INCLUDE "dd_patches.asm"
            INCLUDE "dd_dirty.asm"
            INCLUDE "dd_gameplay.asm"
            INCLUDE "dd_abobo.asm"
            INCLUDE "dd_jeff.asm"
            INCLUDE "dd_controles.asm"
            INCLUDE "dd_latigo.asm"
            INCLUDE "dd_sonido.asm"
            INCLUDE "dd_sfxcas.asm"
            INCLUDE "dd_figfix.asm"
            INCLUDE "cas_resident.asm"
            SAVEBIN "cas_mem.bin",0,65536
''')
sj('dd_cas.asm')
mem=open(os.path.join(D,'cas_mem.bin'),'rb').read()
# page-0 code/vars outside the 0556h+ layer that the loader copies (Abobo, ISPLAYER, mission thunks)
for nm,a,b in (('p0a',0x0040,0x0100),('p0b',0x0400,0x0556),('p0c',0x1C92,0x1D00),('p0d',0x1D40,0x1DC0)):
    open(os.path.join(D,nm+'.bin'),'wb').write(mem[a:b])
sj('cas_extra.asm')
# ---- BLOAD block: original loader with the patched page-0 layer + EXTRA appended
ld=bytearray(open(os.path.join(DD,'loader.bin'),'rb').read())       # C2D0-DB5E
o=0xC36B-0xC2D0; ld[o:o+0x1724]=mem[0x556:0x556+0x1724]
assert ld[0xC368-0xC2D0:0xC36B-0xC2D0]==bytes([0xC3,0x59,0x05])
ld[0xC368-0xC2D0:0xC36B-0xC2D0]=bytes([0xC3,0x5F,0xDB])           # JP EXTRA
ex=open(os.path.join(D,'cas_extra.bin'),'rb').read()
assert len(ld)==0xDB5F-0xC2D0
binimg=bytes(ld)+ex
start,end,exe=0xC2D0,0xC2D0+len(binimg)-1,0xC350
# ---- tape blocks
orig=open(os.path.join(DD,'dd.cas'),'rb').read()
H=bytes([0x1F,0xA6,0xDE,0xBA,0xCC,0x13,0x7D,0x74])
def blk(k): return open(os.path.join(DD,'b%02d.bin'%k),'rb').read()
def tb(data):            # custom block: flag 00 + data + XOR checksum (fixed!)
    x=functools.reduce(lambda a,c:a^c,data,0)
    return b'\x00'+data+bytes([x])
mis=[open(os.path.join(D,'missions','m%d.bin'%n),'rb').read() for n in range(1,8)]
blocks=[blk(0),blk(1),blk(2),
        start.to_bytes(2,'little')+end.to_bytes(2,'little')+exe.to_bytes(2,'little')+binimg,
        tb(open(os.path.join(D,'logo_sc2.bin'),'rb').read()),   # logo de la recreativa en lugar de la pantalla de Xortrapa
        tb(mem[0xE14C:0xE14C+0xEF5]),
        tb(mis[0]),
        tb(mem[0x5B5E:0x5B5E+0x34F0])]
for n,(sk,mk) in enumerate(zip((8,10,12,14,16,18),(9,11,13,15,17,19))):
    stub=blk(sk)[1:1+0x96]
    blocks.append(tb(stub) if sk!=18 else b'\x00'+blk(sk)[1:])   # last stub kept verbatim (160 b)
    blocks.append(tb(mis[n+1]))
blocks.append(tb(blk(20)[1:1+0x550]))
out=bytearray()
for b in blocks:
    while len(out)%8: out.append(0)
    out+=H+b
p=os.path.join(D,'DoubleDragon_optimizado.cas'); open(p,'wb').write(out)
print('CAS %s: %d bytes, %d blocks, BLOAD %04X-%04X exec %04X'%(p,len(out),len(blocks),start,end,exe))
