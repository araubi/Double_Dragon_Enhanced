"""Build the patched post-load memory image + patched mission blocks."""
import subprocess, os, sys, re
D=os.path.dirname(os.path.abspath(__file__)); DD=os.path.join(D,'..','dd')
SJ=os.environ.get('SJASMPLUS','sjasmplus')
mem=open(os.path.join(DD,'mem.bin'),'rb').read()
# figuras rediseñadas (FIGURAS=1): parches (dirección, longitud, datos) de figuras_parches.bin
if os.environ.get('FIGURAS')=='1':
    fp=open(os.path.join(D,'figuras_parches.bin'),'rb').read(); mem=bytearray(mem); i=0
    while i<len(fp):
        a=fp[i]|fp[i+1]<<8; n_=fp[i+2]|fp[i+3]<<8; assert 0x5B5E<=a and a+n_<=0x904E; mem[a:a+n_]=fp[i+4:i+4+n_]; i+=4+n_
    # retrato del marcador: la rutina BAD5 lee la tinta de las 16 primeras líneas de la
    # parte 5B5E (Billy de pie, de espaldas). Copia de la original en E320h (libre) para
    # que el marcador siga mostrando la cara; cada misión apunta allí (abajo, RETRATO)
    # OJO (2026-10-22): E30D-E3B0 es ahora el código de los efectos de la recreativa
    # (dd_sonido.asm); para volver a usar FIGURAS hay que buscarle otro sitio al retrato
    sys.exit('FIGURAS=1: el retrato (E320h) choca con dd_sonido.asm; muévelo antes')
    open(os.path.join(D,'retrato.bin'),'wb').write(open(os.path.join(DD,'mem.bin'),'rb').read()[0x5B5E:0x5BBE])
    open(os.path.join(D,'retrato.inc'),'w').write('            ORG 0E320h          ; zona E31B-E3D0 vaciada arriba\n            INCBIN "retrato.bin"\n')
    mem=bytes(mem); print('figuras rediseñadas aplicadas')
else: open(os.path.join(D,'retrato.inc'),'w').write('')
open(os.path.join(D,'original_mem.bin'),'wb').write(mem)
# ---- colour tables, derived from the converter's own tables
norm=mem[0x0C45:0x0C4D]; bright=mem[0x0C4D:0x0C55]; pf16=mem[0x06C9:0x06D9]
hud=bytes(((bright if a&0x80 else norm)[a&7]<<4) | (bright if a&0x80 else norm)[(a>>3)&7] for a in range(256))
def _pf(a):
    c=pf16[(a | (8 if a&0x80 else 0)) & 0x0F]
    if not a&0x20: return c
    fg=c>>4                                   # bit 5: Jeff -> dark red ink (medium red if the cell is already dark red)
    return 0x81 if fg==6 else 0x61
pf=bytes(_pf(a) for a in range(256))
open(os.path.join(D,'tab_hud.bin'),'wb').write(hud); open(os.path.join(D,'tab_pf.bin'),'wb').write(pf)
# ---- gameplay: scroll trigger sites (positions are the same in patched blocks)
import re as _re
ORIGM={}
for n,k in zip(range(1,8),(6,9,11,13,15,17,19)):
    ORIGM[n]=bytearray(open(os.path.join(DD,'b%02d.bin'%k),'rb').read()[1:1+0x50F6])
SITES=[]   # (mission, offset, side, chk, walk)
for n,b in ORIGM.items():
    for lim,side in ((0x1A,'R'),(0x03,'L')):
        for mm in _re.finditer(bytes([0xDD,0x7E,0x03,0xFE,lim,0x20]),bytes(b)):
            i=mm.start(); off=b[i+6]; W=0x9056+i+7+(off if off<128 else off-256)
            if b[i+7]==0xCD and b[i+10]==0x28:
                SITES.append((n,i,side,b[i+8]|b[i+9]<<8,W))
MAPCHK={}
for n,i,side,chk,W in SITES:
    if ORIGM[n][i+10:i+12]==bytes([0x28,0x6E if side=='R' else 0x36]): MAPCHK[(n,side)]=chk
recs=[]
for idx,(n,i,side,chk,W) in enumerate(SITES):
    recs.append('REC_%d_%04X: call GEN_%s\n            dw %d, %d, %d\n'%(n,0x9056+i,side,chk,W,MAPCHK[(n,side)]))
for k,(lo,hi) in enumerate(((0,1),(5,17),(18,23),(23,26),(2,5),(17,18),(1,2),(26,28)),1):
    open(os.path.join(D,'scrollrec%d.inc'%k),'w').write(''.join(recs[lo:hi]))
print('scroll trampolines:',len(SITES))
# ---- per-mission data for Abobo / player detection
P1S={1:0xAE5D,2:0xAF52,3:0xAF2D,4:0xAF21,5:0xAF71,6:0xAEF4,7:0xAC63}
HITS={}
for n,b in ORIGM.items():
    assert len(_re.findall(_re.escape(bytes([0xFD,0x21,P1S[n]&255,P1S[n]>>8,0x0E,0x01])),bytes(b)))==1,('P1',n)
    i=bytes(b).find(bytes.fromhex('DDE5D5DDE1DD7E0032')); assert i>0; HITS[n]=0x9056+i
open(os.path.join(D,'mistable.inc'),'w').write('MISTABLE:\n'+''.join('            dw %d, %d\n'%(P1S[n],HITS[n]) for n in range(1,8)))
th='MISTHUNK1:  ld a,1\n            call SETMIS\n            jp 9158h\n'
for n in range(2,8): th+='MISTHUNK%d:  ld a,%d\n            call SETMIS\n            ld a,1\n            ld (5B04h),a\n            ret\n'%(n,n)
open(os.path.join(D,'misthunks.inc'),'w').write(th)
# ---- Jeff: per-mission trampolines for the enemy AI's command call
JR=''; JCALL={}
for n,b in ORIGM.items():
    hh=[mm.start() for mm in _re.finditer(rb'\xDD\x35\x04\x79\xCD..\xAF\x32',bytes(b),_re.S)]; assert len(hh)==1,('jcmd',n)
    i=hh[0]+4; JCALL[n]=i; t=b[i+1]|b[i+2]<<8
    JR+='JREC_%d:     call JEFFCMD\n            jp %d\n'%(n,t)
open(os.path.join(D,'jrec.inc'),'w').write(JR)
# ---- background tile routine: mark its cells dirty
DR=''; DCALL={}
for n,b in ORIGM.items():
    hh=[mm.start() for mm in _re.finditer(rb'\xCD..\x06\x10\x1A\x77\x13\x23\x1A\x77\x13\xD5\x11\x1F\x00',bytes(b),_re.S)]; assert len(hh)==1,('tile',n)
    i=hh[0]; DCALL[n]=i; t=b[i+1]|b[i+2]<<8
    DR+='DREC_%d:     call %d\n            jp DMARK\n'%(n,t)
open(os.path.join(D,'drec.inc'),'w').write(DR)
open(os.path.join(D,'dd_ram.asm'),'w').write('''            DEVICE NOSLOT64K
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
            SAVEBIN "patched_mem.bin",0,65536
''')
r=subprocess.run([SJ,'--nologo','--msg=war','--lst=dd_ram.lst','--sym=dd_ram.sym','dd_ram.asm'],cwd=D,capture_output=True,text=True)
print(r.stdout[-2000:],r.stderr[-2000:])
if r.returncode: sys.exit(1)
# ---- Jeff placements (type 0 in an enemy slot; look 00 = Billy's drawing, coloured green)
JEFF_SPAWNS={
  2:[(0x9753,'01004603 0002fa'.replace(' ',''),'00005003 0002fa'.replace(' ',''))],          # mission 2: with the final block
  5:[(0x9745,'01003c03201004','00005003201004'),(0x974C,'01003c0320100e','0000500320100e')],  # mission 4: two on the bridge
  7:[(0x9821,'02005a0320051f','0100320320091f'),   # mission 5B: ... last ordinary enemy,
     (0x9828,'01083c0320071f','02005a0311fc2f'),   # then Willy, near the end of the map (scroll 2Fh, the first step with the arch on
                                                   # screen; Rubén 2026-10-24: 31h made you walk to the very end), out of the
                                                   # arch door (X 0Dh at 31h = 11h at 2Fh: 2 columns per scroll step)
                                                   # (Y FCh: comes down from above; at X 20h he walked out of the wall)
     (0x982F,'0100320320091f','000050030ffc2f'),   # and three Jeffs, also out of the door
     (0x9836,'01083c030afc1f','000050030efc2f'),
     (0x983D,'010032031 0fc1f'.replace(' ',''),'0000500314fc2f')],
}
# ---- energía inicial como en la recreativa (arcade/ENERGIA_GOLPES.md): tabla de la
#      recreativa (6450h, dificultad normal = +4) x 150/64, porque el jugador tiene 150
#      aquí y 64 allí. Columna de la recreativa: carga 1 -> misión 1, 2 -> 2, 3A/3B -> 3,
#      4/5A/5B -> 4. Willy y los Abobos jefe tienen energía propia y la tabla JEFES de
#      rom_musica.asm los reconoce por ella.
SPAWN_TAB={1:(0x9641,11),2:(0x971B,11),3:(0x9703,11),4:(0x96F7,11),5:(0x9745,11),6:(0x9701,6),7:(0x97F0,12)}
ARC_COL={1:0,2:1,3:2,4:2,5:3,6:3,7:3}
E_WILLIAMS=[37,51,66,80]; E_ROPER=[37,56,66,80]; E_LINDA=[28,37,47,56]; E_JEFF=[131,131,140,150]
E_ABO={(0,0):[89,98,112,117],(8,0):[103,112,122,131],     # calvo blanco / moreno
       (0,1):[112,122,126,140],(8,1):[122,131,140,150]}   # con cresta (jefes) blanco / moreno
E_WILLY=150
ABO_JEFE={0x9680,0x9736,0x973D,0x978B}                    # 1: último; 3B: los dos del final; 4: el del final
def energia(n,addr,r):
    t=r[0]&0x0F; c=ARC_COL[n]
    if t==0: return E_JEFF[c]
    if t==1: return (E_ROPER if r[1]==8 else E_WILLIAMS)[c]
    if t==2: return E_WILLY if n==7 else E_LINDA[c]
    assert t==3 and r[1] in (0,8),('abobo',n,hex(addr))
    return E_ABO[(r[1],int(addr in ABO_JEFE))][c]
# ---- symbols for the mission hooks
SYM={}
for line in open(os.path.join(D,'dd_ram.sym')):
    mm=re.match(r'(\S+):\s+EQU\s+0x([0-9A-Fa-f]+)',line)
    if mm: SYM[mm.group(1)]=int(mm.group(2),16)
def le(a): return bytes([a&255,a>>8])
# ---- mission blocks: CAPS -> SHIFT text, renderer + fade hooks
os.makedirs(os.path.join(D,'missions'),exist_ok=True)
for n,k in zip(range(1,8),(6,9,11,13,15,17,19)):
    b=bytearray(open(os.path.join(DD,'b%02d.bin'%k),'rb').read()[1:1+0x50F6])
    i=b.find(b'OR CAPS TO LOAD MISSION ')
    if i>=0:
        j=b.index(0xFF,i); suffix=bytes(b[i+24:j])
        new=b'  OR SHIFT FOR MISSION '+suffix+b'\xff'
        assert len(new)<=j-i+1
        b[i:i+len(new)]=new
        print('mission %d text patched at %04X'%(n,0x9056+i))
    # -- mission entry thunk
    if n==1: assert b[0:3]==bytes.fromhex('CD5891'); b[0:3]=b'\xcd'+le(SYM['MISTHUNK1'])
    else: assert b[0:5]==bytes.fromhex('3E0132045B'); b[0:5]=b'\xcd'+le(SYM['MISTHUNK%d'%n])+b'\x00\x00'
    # -- sound on every hit
    i=bytes(b).find(bytes.fromhex('2008FD8608FD7708')); assert i>0,('snd',n)
    t=bytes(b).find(bytes.fromhex('3AD1E3FEFF'),i); assert 0<t-(i+10)<0x80
    assert b[i+8]==0x18 and b[i+9]==(t+11-(i+10)),('snd jr',n)
    b[i+9]=t-(i+10)
    # -- efectos de la recreativa (dd_sonido.asm)
    def uno(rx,nombre,obligado=True):
        ms=list(re.finditer(rx,bytes(b),re.S)); assert len(ms)==(1 if obligado else len(ms)) and len(ms)<=1,(nombre,n,len(ms))
        return ms[0] if ms else None
    mm=uno(rb'\x3a\xd1\xe3\xfe\xff\x20\x04\xaf\x32\xd1\xe3','hitsnd')       # golpe: puñetazo o patada
    j=mm.start()+7; b[j:j+4]=b'\xcd'+le(SYM['HITSND'])+b'\x00'
    mm=uno(rb'\xdd\x36\x08\x00\xdd\x36\x09\x3c(\xdd\x7e\x0f\xfe\x02\x28\x06)?\xdd\x34\x04\xdd\x34\x04\xdd\x7e\x11\xa7\x20\x06\xdd\x36\x09\xff','land')
    j=mm.start(); b[j:j+8]=b'\xcd'+le(SYM['LAND'])+b'\x00'*5                # derribado en el suelo / muerte
    mm=uno(rb'\x32\xd1\xe3\xdd\xcb\x0a\x86\xfd\xcb\x00\x86','derribo')      # el golpe del derribo ya suena en HITSND
    j=mm.start(); b[j:j+3]=b'\x00\x00\x00'
    mm=uno(rb'\x1e\x02\xcd..\xdd\xcb\x0a\xee','rodillazo')       # rodillazo al agarrado
    j=mm.start()+5; b[j:j+4]=b'\xcd'+le(SYM['KNEE'])+b'\x00'
    mm=uno(rb'\x21..\xdd\xcb\x0a\x76\x28\x03\x21..\x4b\xc3','rodillazo anim')   # patada con alguien agarrado
    j=mm.start()+3; b[j:j+6]=b'\x00\xcd'+le(SYM['KNEEB'])+b'\x28\x03'
    if n<7:
        mm=uno(rb'\xdd\x34\x08\xdd\x7e\x09\xfe\x02\xda..\xdd\x7e\x08\xfe\x01\x20','vuelo')   # bate, látigo, cuchillo; bote de bidón y roca
        j=mm.start(); b[j:j+3]=b'\xcd'+le(SYM['FLYHK'])
        mm=uno(rb'\xfd\x7e\x0b\xfe\x0a\xca(..)\xfe\x0b\xca(..)\xdd\x36\x03\x80','cuchillo') # cuchillo parado
        t=mm.group(1); assert t==mm.group(2); o=(t[0]|t[1]<<8)-0x9056
        assert bytes(b[o:o+13])==bytes.fromhex('dd360800dd360b00dd360a01c9'),('kkick',n)
        b[mm.start(1):mm.start(1)+2]=le(SYM['KKICK']); b[mm.start(2):mm.start(2)+2]=le(SYM['KKICK'])
    if n>1:
        mm=uno(rb'\xdd\x36\x09\xff\xdd\x36\x08\x10\xdd\x36\x11\x00\xc9','agua')  # cae al agua / foso
        j=mm.start(); b[j:j+4]=b'\xcd'+le(SYM['FALLW'])+b'\x00'
    if n==5:
        # puerta del final de la misión 4: el último paso de la animación (B144h, 4x3 baldosas)
        # pedía abajo a la derecha la baldosa 5Dh, que no existe (detrás del juego de baldosas
        # empieza otra tabla) y salía basura. Va la 5Bh, el poste derecho, hasta el suelo.
        mm=uno(rb'\x58\x00\x59\x5a\x00\x5b\x5a\x00\x5b\x5c\x00\x5d','puerta abierta')
        assert 0x9056+mm.start()==0xB144
        b[mm.start()+11]=0x5B
    if n==6:
        mm=uno(rb'\x3a\x47\xb1\xa7\xc8\xfe\x06\xd0','piedras fase')
        mm=uno(rb'\x3d\x87\x5f\x57\xcd..\xed\x43\x48\xb1\xc9','piedras')       # piedras de la pared
        j=mm.start()+7; b[j:j+4]=b'\xcd'+le(SYM['STONE'])+b'\x00'
        # piedras: arrancan al acercarse y paran al pasarlas (STGATE); repintado solo al cambiar (STDR)
        assert bytes(b[0xA276-0x9056:0xA278-0x9056])==b'\xaf\xc9'
        mm=uno(rb'\x21\x80\x80\x22\x48\xb1\xe1(\x3a\x4c\xc8\xa7\xc0)\xd5\xe5\x3e\x05','piedras puerta')
        assert 0x9056+mm.start(1)==0xB0C2
        j=mm.start(1); b[j:j+5]=b'\xcd'+le(SYM['STGATE'])+b'\xc0\x00'
        mm=uno(rb'\x3e\x0a\x32\xb9\xb1\xe1\xd1(\xcd\x9c\xb1)\x3a\x47\xb1','piedras dibujo')
        j=mm.start(1); b[j:j+3]=b'\xcd'+le(SYM['STDR'])
    if n==7:
        mm=uno(rb'\xaf\x32\xd1\xe3\xcd\x01\xe3\x3e\x10\xc9','metralleta')
        j=mm.start(); b[j:j+7]=b'\x3e\x16\x32\xd1\xe3\x00\x00'
        mm=uno(rb'\x3e\x02\x32\xd1\xe3\xcd\x01\xe3','zap')
        b[mm.start()+1]=0x18
    print('mission %d: efectos de la recreativa enganchados'%n)
    # -- elbow
    hits=[mm.start() for mm in re.finditer(rb'\xdd\x7e\x02\x32..\xdd\xe1',bytes(b),re.S)]; assert len(hits)==1,('elb',n,hits)
    assert b[hits[0]-6:hits[0]-3]==b'\xdd\x7e\x01' and b[hits[0]-3]==0x32,('elb dmg',n)
    b[hits[0]:hits[0]+3]=b'\xcd'+le(SYM['ELB'])
    # -- scroll thresholds
    for lim,side,newcp,newjr in ((0x1A,'R',0x18,0x38),(0x03,'L',0x06,0x30)):
        for mm in list(re.finditer(bytes([0xDD,0x7E,0x03,0xFE,lim,0x20]),bytes(b))):
            j=mm.start(); b[j+4]=newcp; b[j+5]=newjr
            if b[j+7]==0xCD and b[j+10]==0x28:
                b[j+8:j+10]=le(SYM['REC_%d_%04X'%(n,0x9056+j)])
    # -- checks that wrote absolute X values -> relative
    for rx,first,second in ((rb'\xdd\x36\x03\x1b\x11\x07\x05\xcd..\xdd\x36\x03\x1a\xc9',b'\xdd\x34\x03\x00',b'\xdd\x35\x03\x00'),
                            (rb'\xdd\x36\x03\x02\x11\x06\x02\xcd..\xdd\x36\x03\x03\xc9',b'\xdd\x35\x03\x00',b'\xdd\x34\x03\x00')):
        hh=[mm.start() for mm in re.finditer(rx,bytes(b),re.S)]; assert len(hh)==1,('chk',n,len(hh))
        b[hh[0]:hh[0]+4]=first; b[hh[0]+10:hh[0]+14]=second
    for pat,rep in ((b'\xdd\x36\x03\x1b\xdd\x35\x04',b'\xdd\x34\x03\x00'),(b'\xdd\x36\x03\x1a\x3e\x08',b'\xdd\x35\x03\x00'),
                    (b'\xdd\x36\x03\x02\xdd\x35\x04',b'\xdd\x35\x03\x00'),(b'\xdd\x36\x03\x03\x3e\x08',b'\xdd\x34\x03\x00')):
        hh=[mm.start() for mm in re.finditer(re.escape(pat),bytes(b))]
        assert len(hh)==1,('abs',n,pat.hex(),len(hh))
        b[hh[0]:hh[0]+4]=rep
    # -- Jeff: "type 0" tests in the hit code become "is a player" tests
    hh=[mm.start() for mm in re.finditer(rb'\xDD\x7E\x0F\xA7\x28',bytes(b))]
    hh=[j for j in hh if bytes(b).find(b'\xFD\x7E\x0F\xA7\xC0',j,j+20)>0]; assert len(hh)==1,('jatt',n,hh)
    b[hh[0]:hh[0]+4]=b'\xcd'+le(SYM['ISPX'])+b'\x00'
    hh=[mm.start() for mm in re.finditer(rb'\xFD\x7E\x0F\xA7[\xC0\x28]',bytes(b))]; assert len(hh) in (2,3),('jtgt',n,hh)
    for j in hh: b[j:j+4]=b'\xcd'+le(SYM['ISPY'])+b'\x00'
    j=JCALL[n]; assert b[j]==0xCD; b[j+1:j+3]=le(SYM['JREC_%d'%n])
    j=DCALL[n]; assert b[j]==0xCD; b[j+1:j+3]=le(SYM['DREC_%d'%n])
    rp=bytes.fromhex('7D12137C1213E53E'); hits=[mm.start() for mm in re.finditer(re.escape(rp),bytes(b))]
    assert len(hits)==1,('render',n,hits); b[hits[0]:hits[0]+6]=b'\xcd'+le(SYM['MARK'])+b'\x00\x00\x00'
    fp=bytes.fromhex('21002C010014'); hits=[mm.start() for mm in re.finditer(re.escape(fp),bytes(b))]
    assert len(hits)==1,('fade',n,hits); b[hits[0]:hits[0]+3]=b'\xcd'+le(SYM['FADEHOOK'])
    print('mission %d hooks: render %04X fade %04X'%(n,0x9056+b.find(b'\xcd'+le(SYM['MARK'])),0x9056+hits[0]))
    # -- al completar una misión se carga la siguiente sin preguntar (antes: disparo = repetir
    #    la misma, SHIFT = cargar la siguiente). 5B1B queda a 0 para que no salga "OR SHIFT".
    if n<=6:
        i=bytes(b).find(bytes.fromhex('3E01321B5B')); assert i>0,('fin',n)
        ld=bytes(b).find(bytes.fromhex('E1373EFFDD2160EA')); assert ld>0,('carga',n)
        jj=[j for j in range(i,i+80) if b[j]==0xC3 and b[j+1:j+3] in (le(0x9056),le(0x9088))]; assert jj,('fin jp',n)
        b[i+1]=0
        b[jj[0]+1:jj[0]+3]=le(0x9056+ld+1)
        print('mission %d: fin %04X -> carga %04X'%(n,0x9056+jj[0],0x9056+ld+1))
    # -- látigo: solo lo recogen Linda y los jugadores (dd_latigo.asm)
    ms=list(re.finditer(rb'\xcd(..)\x20\x0f\x3a..\xdd\x77\x07\xd1\xc1\xdd\xe1\xdd\x71\x07',b,re.S)); assert len(ms)==1,('latigo',n)
    t=ms[0].group(1)[0]|ms[0].group(1)[1]<<8; assert bytes(b[t-0x9056:t-0x9056+5])==bytes.fromhex('dd7e07a7c9'),('latigo',n)
    b[ms[0].start()+1:ms[0].start()+3]=le(SYM['WHIPCHK'])
    # -- látigo (2): los enemigos tampoco van a por él (IA que elige objeto). Antes: tipo 3
    #    nunca, Linda (tipo 2) solo el látigo, los demás cualquiera. Ahora los demás todo
    #    menos el látigo (Rubén, 2026-10-25). «tipo xor 2, por 2» deja < 2 solo a Linda.
    if n<7:
        mm=uno(rb'\xdd\x7e\x07\xa7\x20.(\xdd\x7e\x0f\xfe\x03\x28(.)\xfe\x02\x20\x07\xfd\x7e\x09\xfe\x01\x20.)','latigo ia')
        j=mm.start(1); no=j+7+b[mm.start(2)]
        new=bytes.fromhex('fd7e093d dd7e0f 2003 ee02 87 fe02')
        b[j:j+18]=new+bytes([0x30,(no-(j+len(new)+2))&255])+b'\x00\x00'
        print('mission %d: latigo ia %04X'%(n,0x9056+j))
    # -- agarrar de los pelos: tampoco a Jeff (GRABCHK); en la misión 2 Xortrapa exigía
    #    además la misma Y exacta del agarrado, y el agarre casi nunca salía: se quita
    ms=list(re.finditer(rb'\xfd\x86\x0a\xe6\x01\x28.\xfd\x7e\x0f\xfe\x02\x30.\xfd\x7e\x08\xfe\x04\x38.\xdd\x7e\x07\xa7\x20.',b,re.S)); assert len(ms)==1,('agarre',n)
    g=ms[0].start()+7; b[g:g+5]=b'\xcd'+le(SYM['GRABCHK'])+b'\x00\x00'
    e=ms[0].end()
    if bytes(b[e:e+6])==bytes.fromhex('dd7e04fdbe04'):
        assert n==2 and b[e+6]==0x20; b[e+6:e+8]=b'\x00\x00'
    print('mission %d: agarre %04X'%(n,0x9056+g))
    # -- objetos: HL recuperado tras su rutina de movimiento (OBJHL, dd_jeff.asm)
    if n<7:
        mm=uno(rb'\xc5\xe5(?:\xdd\x7e\x00\xa7\x28.)?\x79\x32..\xcb\x96\xcb\x8e\xdd\xcb\x0b\x46\x28\x09\xcd..(\xdd\xcb\x0b\x46)\x20\x0b','objeto hl')
        j=mm.start(1)
        b[j:j+4]=b'\xcd'+le(SYM['OBJHL'])+b'\x00'
        print('mission %d: OBJHL en %04X'%(n,0x9056+j))
        mm=uno(rb'\xdd\x5e\x02\xcd..(\xa7\x28\x04\x3c\xdd\x77\x00)','objeto cae')
        j=mm.start(1)
        b[j:j+7]=b'\xcd'+le(SYM['OBJCAE'])+b'\x00'*4
        print('mission %d: OBJCAE en %04X'%(n,0x9056+j))
    # -- Jeff in the spawn tables (record: type, look, energy, ?, X, Y, trigger)
    J=JEFF_SPAWNS.get(n,[])
    for addr,old,new in J:
        o=addr-0x9056; assert bytes(b[o:o+7])==bytes.fromhex(old),('spawn',n,hex(addr),bytes(b[o:o+7]).hex())
        b[o:o+7]=bytes.fromhex(new)
    a0,k=SPAWN_TAB[n]
    for i in range(k):
        addr=a0+7*i; o=addr-0x9056; r=b[o:o+7]; assert r[3]==3,('registro',n,hex(addr))
        e=energia(n,addr,r)
        print('mission %d: enemigo %04X tipo %02X aspecto %02X energía %d -> %d'%(n,addr,r[0],r[1],r[2],e))
        b[o+2]=e
    assert b[a0-0x9056+7*k+3]!=3,('tabla más larga',n)
    # -- misión 2: el mapa de alturas de Xortrapa tiene 6 casillas con basura en la reja del
    #    principio (45 00 3D 75 28 28 en vez de 09, pared). Una de altura 4 hacía que un salto
    #    junto a la reja aterrizase encima de ella, y al andar fuera de esa casilla, caída mortal.
    if n==2:
        mm=uno(rb'\x09\x09\x45\x00\x3d\x75\x28\x28\x09\x09','reja')
        j=mm.start()+2; b[j:j+6]=b'\x09'*6
        # -- los enemigos que esperan turno no se mueven con el scroll vertical (A122h: primero
        #    se mira si la ficha está activa, como ya se hacía con la X). Si no, su fila de
        #    salida dependía de cuándo se cargaron y al final de la misión uno salía con los pies
        #    sobre el vacío y caía hasta morir (repetición de Rubén, 2026-10-24; ya en el original).
        #    Primer intento: subirlo al suelo al aparecer, en C700h; esos ceros eran el bloque
        #    negro de la pared de la escalera y salía ruido azul. No usar C6FE-C747h.
        mm=uno(re.escape(bytes.fromhex('7add8604dd7704dd7e00a7c87bdd8603dd7703c9')),'scroll en espera')
        j=mm.start(); b[j:j+20]=bytes.fromhex('dd7e00a7c87add8604dd77047bdd8603dd7703c9')
        print('mission 2: scroll vertical solo para fichas activas %04X'%(0x9056+j))
    # -- la misma basura (DF7F-DF84) cae dentro del mapa de alturas en la misión 1 (fila 8, al
    #    final del mapa: el jugador se subía al seto; repetición de Rubén 2026-10-24) y en la 3A
    #    (fila 7). Se pone el valor de las casillas de al lado (01 y 50). En la 3B y la 4 la
    #    dirección cae fuera de su mapa (filas 15 y 31) y no se lee (mapr.py).
    if n in (1,3):
        v=bytes([{1:1,3:0x50}[n]])
        mm=uno(re.escape(v*2+b'\x45\x00\x3d\x75\x28\x28'+v*2),'basura DF7F')
        j=mm.start()+2; b[j:j+6]=v*6
    if os.environ.get('FIGURAS')=='1':        # RETRATO: ld de,5B5Fh -> ld de,E321h
        j=bytes(b).find(b'\x11\x5F\x5B\xED\x43'); assert j>=0 and bytes(b).count(b'\x11\x5F\x5B\xED\x43')==1,('retrato',n)
        b[j+1:j+3]=b'\x21\xE3'
    open(os.path.join(D,'missions','m%d.bin'%n),'wb').write(b)
    if n==1:
        pm=bytearray(open(os.path.join(D,'patched_mem.bin'),'rb').read()); pm[0x9056:0x9056+len(b)]=b
        open(os.path.join(D,'patched_mem.bin'),'wb').write(pm)
