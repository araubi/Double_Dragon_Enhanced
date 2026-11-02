"""Build the ASCII8 MegaROM."""
import subprocess, os, sys, re
D=os.path.dirname(os.path.abspath(__file__)); DD=os.path.join(D,'..','dd')
SJ=os.environ.get('SJASMPLUS','sjasmplus')
MSX2=bool(os.environ.get('MSX2'))     # ROM MSX2: lógica MSX1 + motor SCREEN 5 (dd_msx2.asm, m2render.asm)
M2DIR=os.path.join(D,'..','..','..','motor')   # tiras y paleta del motor (prep.py)
def sj(src, lst, raw=None):
    r=subprocess.run([SJ,'--nologo','--msg=war']+(['-DPROF'] if os.environ.get('PROF') else [])+['--lst='+lst,'--sym='+lst.replace('.lst','.sym')]+(['--raw='+raw] if raw else [])+[src],cwd=D,capture_output=True,text=True)
    if r.returncode or r.stdout.strip() or r.stderr.strip(): print(r.stdout[-3000:],r.stderr[-3000:])
    if r.returncode: sys.exit(1)
def syms(f):
    out={}
    for line in open(os.path.join(D,f)):
        m=re.match(r'(\S+):\s+EQU\s+0x([0-9A-Fa-f]+)',line)
        if m: out[m.group(1)]=int(m.group(2),16)
    return out
subprocess.run([sys.executable,'build_ram.py'],cwd=D,check=True,capture_output=True)
mis=[open(os.path.join(D,'missions','m%d.bin'%n),'rb').read().replace(b'REWIND TO START ',b'  RESTARTING... ') for n in range(1,8)]
stubs=[open(os.path.join(DD,'b%02d.bin'%k),'rb').read()[1:1+0x96] for k in (8,10,12,14,16,18)]
extra=open(os.path.join(DD,'b20.bin'),'rb').read()[1:1+0x550]
scr=open(os.path.join(D,'logo_sc2.bin'),'rb').read()   # logo de la recreativa (tools/logo) en lugar de la pantalla de Xortrapa
assert len(scr)==0x3000
P0_LEN=0x1DC0   # page 0 incl. the code at 1D40h-1DBFh
# ---- layout (sizes only)
order=[('P0',None,P0_LEN,0),('SCR',scr,0x3000,0),('SHARED',None,0xF041-0xE14C,0xE14C),('CORE',None,0x904E-0x5B5E,0x5B5E)]   # CORE = bloque de cinta 5B5E-904D (en 8F6E-904D, Abobo tumbado)
order+=[('M%d'%(n+1),mis[n],0x50F6,0x9056) for n in range(7)]
order+=[('ST%d'%(n+2),stubs[n],0x96,0xEA60) for n in range(6)]
order+=[('EXTRA',extra,0x550,0xEE48)]
order+=[('HIGH',None,0x800,0xF400)]      # música durante el juego (rom_musica.asm)
if MSX2: order+=[('M2RES',None,0xD8,0xFF00)]   # código residente MSX2 (m2boot.inc)
order+=[('SPRA',None,0x80,0x2440),('SPRB',None,0x80,0x2540),('SPRC',None,0x80,0x2600),('SPRD',None,0x68,0xF398),('SPRE',None,0x20,0x20A0),('SPRF',None,0x20,0x21A0),('SPRG',None,0x20,0x22A0)]   # sprites de los jugadores (dd_sprites.asm)
lay={}; off=0x2000
for name,data,size,dest in order:
    lay[name]=(off,size,dest); off+=size
# efectos de sonido de la recreativa (tools/efectos.py): datos para mus_player.asm
sys.path.insert(0,os.path.join(D,'..','tools')); import efectos; efectos.inc(os.path.join(D,'sfx_data.inc'))
# músicas: un banco de 8 KB por canción, con su copia del reproductor (ejecuta en 4000h)
SONGS=[('01','mus_data.inc',4238.8/44100),('02',),('06',),('07',),('08',),('09',),('04',),('03',)]
bank=(off+0x1FFF)>>13; musbins=[]; mb=''
for sg in SONGS:
    sid=sg[0]; inc=sg[1] if len(sg)>1 else 'mus_%s.inc'%sid
    data=open(os.path.join(D,inc)).read()
    tick=sg[2] if len(sg)>2 else int(re.search(r'MUS_TICK EQU (\d+)',data).group(1))/1e5
    cur='STEP50 EQU %d\nSTEP60 EQU %d\n'%(round(65536*0.02/tick),round(65536/59.92/tick))
    assert max(round(65536*0.02/tick),round(65536/59.92/tick))<65536,(sid,'paso más corto que un cuadro')
    open(os.path.join(D,'mus_cur.inc'),'w').write(cur+data.replace('MUS_TICK EQU','MUS_TICK_ EQU').replace('WAH EQU','WAH_ EQU'))
    open(os.path.join(D,'mus_opt.inc'),'w').write('            DEFINE WAH\n' if 'WAH EQU 1' in data else '')
    sj('mus_player.asm','mus_%s.lst'%sid,'mus_%s.bin'%sid)
    b=open(os.path.join(D,'mus_%s.bin'%sid),'rb').read(); assert len(b)<=0x2000,(sid,len(b))
    musbins.append((bank,b)); mb+='MB_%s EQU %d\n'%(sid,bank); bank+=1
off=(bank-1)*0x2000+len(musbins[-1][1])
open(os.path.join(D,'musbanks.inc'),'w').write(mb)
if MSX2:
    BK_M2=bank; BK_STR=bank+1
    import m2data; strips,m2figs,BK_FIG=m2data.gen(D,M2DIR,mis[0][0xB07E-0x9056:0xB07E-0x9056+128*9],BK_STR)
    open(os.path.join(D,'m2banks.inc'),'w').write('BK_M2 EQU %d\nBK_STR EQU %d\nBK_FIG EQU %d\n'%(BK_M2,BK_STR,BK_FIG))
    off=BK_FIG*0x2000+len(m2figs)
MUSBANK=musbins[0][0]
# tabla de volteo (E512h) para dd_figuras.asm
_t=open(os.path.join(D,'original_mem.bin'),'rb').read()[0xE512:0xE612]
open(os.path.join(D,'fliptab.inc'),'w').write(''.join('            db %s\n'%','.join('%d'%x for x in _t[i:i+16]) for i in range(0,256,16)))
# puntos de sondeo de la música en cada misión (rom_musica.asm): stubs en F400h+
PATS={'draw':(rb'\x87\xc8\x32..\x01..(\x3e.\xb9)\x30\x0a\xc5\x01..\xeb\x09\xeb\xc1\x18',1),
      'rest':(rb'\x21..\x7e\xa7\xc8\x47(\xc5\x2a..)\x2b\x2b\x22',1),     # cada figura
      'hudt':(rb'(\x3e\x01\x32..)\x3a\x18\x5b\x21\x06\x5b',1)}
polls=''; sites=[]
for n in range(1,8):
    b=mis[n-1]
    for k,(rx,cnt) in PATS.items():
        ms=list(re.finditer(rx,b,re.S)); assert len(ms)==cnt,(n,k,len(ms))
        g=ms[0]; o=g.start(1); disp=g.group(1); site=0x9056+o
        for a in range(site+1,site+len(disp)):    # nada escribe en los bytes desplazados
            assert not re.search(re.escape(bytes([0x32,a&255,a>>8])),b),(n,k,hex(a))
        lab='PS_%s_%d'%(k,n)
        polls+='%s:  call MUSPOLL\n            db %s\n            jp %d\n'%(lab,','.join('%d'%x for x in disp),site+len(disp))
        sites.append((n,o,lab))
# bucle principal de cada misión: cada CALL pasa por un sondeo (stub: CALL MUSPOLL / JP destino)
sys.path.insert(0,os.path.join(D,'..','tools')); import z80dis as Z
mainc={}; stubt={}
for n in range(1,8):
    b=mis[n-1]; mem=bytes(0x9056)+b+bytes(0x10000-0x9056-len(b)); Dz=Z.Dis(mem,0)
    i=b.find(b'\xcd\x12\xe6'); site=0x9056+i
    j=i
    while not (b[j]==0xc3 and site-0x30<=(b[j+1]|b[j+2]<<8)<=site): j+=1
    start=b[j+1]|b[j+2]<<8; end=0x9056+j; pc=start; lst=[]
    while pc<end:
        t,l,f,tg=Dz.dec(pc)
        if mem[pc]==0xcd:
            tgt=mem[pc+1]|mem[pc+2]<<8
            if tgt!=0xE612:
                for a in (pc+1,pc+2):
                    assert not re.search(re.escape(bytes([0x32,a&255,a>>8])),b),(n,'main',hex(a))
                lab=stubt.setdefault(tgt,'PM_%04X'%tgt); lst.append((pc,lab))
        pc+=l
    assert pc==end and 8<=len(lst)<=30,(n,hex(start),hex(end),len(lst))
    mainc[n]=lst
# GAME OVER con créditos (misiones 2-7): sigue la misión sin pasar por SETMIS -> su canción otra vez
contp={}
for n in range(2,8):
    b=mis[n-1]; ms=list(re.finditer(rb'\x20\x12\x21\x88\x48.{15}\xcd..(\xc3..)',b,re.S)); assert len(ms)==1,(n,'cont')
    o=ms[0].start(1); tgt=b[o+1]|b[o+2]<<8; contp[n]=o
    polls+='PS_cont_%d:  call MUSRESUME\n            jp %d\n'%(n,tgt)
for tgt,lab in sorted(stubt.items()): polls+='%s:  call MUSPOLL\n            jp %d\n'%(lab,tgt)
open(os.path.join(D,'mus_polls.inc'),'w').write(polls)
romsize=1<<(off-1).bit_length()
assert romsize<=(0x100000 if MSX2 else 0x40000), hex(off)
def item(name):
    o,size,dest=lay[name]; return '            db %d\n            dw %d, %d, %d\n'%(o>>13,o&0x1FFF,dest,size)
inc='NBOOTITEMS EQU 11\nBOOTITEMS:\n'+item('HIGH')+item('SHARED')+item('CORE')+item('M1')+item('SPRA')+item('SPRB')+item('SPRC')+item('SPRD')+item('SPRE')+item('SPRF')+item('SPRG')
open(os.path.join(D,'romitems.inc'),'w').write(inc)
# el resto de tablas, en la zona alta (ya cargada cuando se piden misiones)
inc='STUBTAB:\n'+''.join(item('ST%d'%n) for n in range(2,8))
inc+='MISTAB:\n'+''.join(item('M%d'%n) for n in range(2,8))+'EXTRAITEM:\n'+item('EXTRA')
open(os.path.join(D,'romitems2.inc'),'w').write(inc)
o=lay['SCR'][0]; p=lay['P0'][0]
open(os.path.join(D,'romboot.inc'),'w').write('SCR_BANK EQU %d\nSCR_OFS EQU %d\nP0_BANK EQU %d\nP0_OFS EQU %d\nP0_LEN EQU %d\n'%(o>>13,o&0x1FFF,p>>13,p&0x1FFF,P0_LEN))
open(os.path.join(D,'dd_rom.asm'),'w').write('''            DEVICE NOSLOT64K
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
            INCLUDE "dd_figfix.asm"
            INCLUDE "rom_resident.asm"
            INCLUDE "rom_musica.asm"
            INCLUDE "dd_sprites.asm"
'''+('            INCLUDE "dd_msx2.asm"\n' if MSX2 else '')+'''            SAVEBIN "rom_mem.bin",0,65536
''')
sj('dd_rom.asm','dd_rom.lst')
S=syms('dd_rom.sym')
open(os.path.join(D,'ressyms.inc'),'w').write(''.join('%s EQU %d\n'%(k,S[k]) for k in ('RESBOOT','SLOT_CART','SLOT_RAM1','SLOT_RAM2')))
if MSX2:
    o=lay['M2RES'][0]
    open(os.path.join(D,'m2boot0.inc'),'w').write('            ld a,(002Dh)\n            ld (0C015h),a\n')
    open(os.path.join(D,'m2boot.inc'),'w').write('            ld hl,.m2item\n            call BLOAD_ITEM\n            call BCOPY\n            ld a,(0C015h)\n            ld (0FF00h),a\n            jp RESBOOT\n.m2item:    db %d\n            dw %d, 0FF00h, %d\n'%(o>>13,o&0x1FFF,lay['M2RES'][1]))
    open(os.path.join(D,'m2syms.inc'),'w').write(''.join('%s EQU %d\n'%(k,S[k]) for k in ('M2VER','M2ST','M2TK','M2BASE','M2W')))
    sj('m2render.asm','m2render.lst')
else:
    for f in ('m2boot0.inc','m2boot.inc'): open(os.path.join(D,f),'w').write('')
sj('rom_boot.asm','rom_boot.lst')
# parches de la música en las misiones (solo ROM)
S2={}
for line in open(os.path.join(D,'dd_rom.sym')):
    mm=re.match(r'(\S+):\s+EQU\s+0x([0-9A-Fa-f]+)',line)
    if mm: S2[mm.group(1)]=int(mm.group(2),16)
le=lambda v: bytes([v&255,v>>8])
FIX={'delay':(rb'\x1e.(\x01\xff\xff)\x0b\x78\xb1\x20\xfb\x1d\x20\xf5\xc9',b'\xc3'+le(S2['DELAY'])),
     'compl':(rb'(\x3e\x00\x32\x1b\x5b)',b'\xcd'+le(S2['MCOMPL'])+b'\0\0'),
     'gover':(rb'(\x21\x4b\x48)\xdd\x21',b'\xcd'+le(S2['GOVER'])),
     'ends':(rb'(\x21\x42\x48)\xdd\x21',b'\xcd'+le(S2['ENDSONG'])),
     'endw':(rb'\x3e\x01\x32\x08\x5b(\xcd..)\xc3',b'\xcd'+le(S2['ENDWAIT']))}
for n in range(1,8):
    b=bytearray(mis[n-1])
    for nn,o,lab in sites:
        if nn==n: b[o:o+3]=b'\xc3'+le(S2[lab])     # los bytes desplazados que sobran no se ejecutan
    for pc,lab in mainc[n]: b[pc-0x9056+1:pc-0x9056+3]=le(S2[lab])
    if n in contp: b[contp[n]+1:contp[n]+3]=le(S2['PS_cont_%d'%n])
    for k,(rx,new) in FIX.items():
        ms=list(re.finditer(rx,bytes(b),re.S))
        want=1 if (k not in ('compl','ends','endw') or (k=='compl')==(n<7)) else 0
        assert len(ms)==want,(n,k,len(ms))
        for g in ms: b[g.start(1):g.start(1)+len(new)]=new
    # dibujo de figuras (dd_figuras.asm): una llamada por línea en vez de una por byte
    if not os.environ.get('NOFIG'):      # NOFIG=1: sin este parche (para comparar)
        fs=list(re.finditer(rb'\xcb\x5e\x21(..)\x28\x03\x21(..)\x22(..)\x79\x32',bytes(b),re.S)); assert len(fs)==1,(n,'fsel')
        fr=list(re.finditer(rb'\x01\x00\x00(\x23\x23\x3e\x1f\xb9\x38\x07\x2b\x2b\xcd(..)\x23\x13\x0c\x10\xef)\xcd',bytes(b),re.S)); assert len(fr)==1,(n,'frow')
        fs,fr=fs[0],fr[0]; op=fr.start(2)+0x9056
        assert fs.group(3)==le(op) and fr.group(2) in (fs.group(1),fs.group(2)),(n,'fsel/frow')
        assert len(re.findall(re.escape(b'\x22'+le(op)),bytes(b)))==1,(n,'frow writers')
        o=fr.start(1); call=o+0x9056+1
        b[o:fr.end(1)]=(b'\xcd'+le(S2['DRAWM'])+b'\x18'+bytes([fr.end(1)-(o+5)])).ljust(fr.end(1)-o,b'\0')
        b[fs.start(1):fs.end(1)]=le(S2['DRAWM']); b[fs.start(2):fs.end(2)]=le(S2['DRAWI']); b[fs.start(3):fs.end(3)]=le(call)
        fl=list(re.finditer(rb'\x11..\x3e.(\x08\x21\x12\xe5\x1a\x06\x00\x4f\x09\x7e\x12\x13\x08\x3d\x20\xf0)',bytes(b),re.S)); assert len(fl)==1,(n,'flip')
        o=fl[0].start(1); b[o:fl[0].end(1)]=(b'\xcd'+le(S2['FLIP'])+b'\x18'+bytes([fl[0].end(1)-(o+5)])).ljust(fl[0].end(1)-o,b'\0')
        # sprites de los jugadores (dd_sprites.asm): la rutina de cada figura la elige FIGSEL
        o=fs.start(); assert fs.end(2)-o==10
        b[o:o+10]=b'\xcd'+le(S2['FIGSEL'])+b'\x18\x05'+b'\0'*5
        # marcador: cara del jugador 2 ya no en negativo (solo volteada: ~(~flip(tinta)))
        r=list(re.finditer(rb'\xcd(..)\x08\x1b\x1a\x13\xcd\1\xd9\x4f\x08\xa1\xd9\x77\x2d\xc9',bytes(b),re.S)); assert len(r)==1,(n,'cara2')
        o=r[0].start(); b[o+3:o+7]=b'\x2f\x77\x2d\xc9'
        # y caras con el color de su sprite: tinta 3 (celeste) y 2 (rojo); TAB_HUD en dd_sprites.asm
        t=bytes.fromhex('77d777777766ccccccee7777d777777777d777777777444444667777d7777777'); i=bytes(b).find(t); assert i>=0 and bytes(b).find(t,i+1)<0,(n,'atr')
        for k,v in ((0,0x37),(1,0xd3),(11,0x22),(12,0xd2),(16,0x37),(17,0xd3),(27,0x22),(28,0xd2)): b[i+k]=v
    if MSX2 and n==1:      # SCREEN 5: las partes de las figuras no se preparan (M2PART)
        r=list(re.finditer(rb'\xdd\x7e\x01\xdd\x5e\x02\xdd\x56\x03\xcd(..)\xdd\x7e\x04\xdd\x5e\x05\xdd\x56\x06\xcd(..)',bytes(b),re.S)); assert len(r)==1,(n,'part')
        assert r[0].group(1)==r[0].group(2)==le(0xBC0A),(n,'part target')
        for k in (1,2): b[r[0].start(k):r[0].end(k)]=le(S2['M2PART'])
    mis[n-1]=bytes(b)
    open(os.path.join(D,'missions','rom_m%d.bin'%n),'wb').write(mis[n-1])
rm=bytearray(open(os.path.join(D,'rom_mem.bin'),'rb').read())
rm[0x9056:0x9056+0x50F6]=mis[0]
open(os.path.join(D,'rom_mem.bin'),'wb').write(rm)
rom=bytearray(b'\xff'*romsize)
b0=open(os.path.join(D,'rom_bank0.bin'),'rb').read(); rom[0:len(b0)]=b0
for name,data,size,dest in order:
    o=lay[name][0]
    if name[0]=='M' and name[1:].isdigit(): data=mis[int(name[1:])-1]     # con los parches de la música
    if data is None:
        data=bytes(rm[0:P0_LEN]) if name=='P0' else bytes(rm[dest:dest+size])
    assert len(data)==size,(name,len(data),size)
    rom[o:o+size]=data
for bk,b in musbins: rom[bk*0x2000:bk*0x2000+len(b)]=b
if MSX2:
    code=open(os.path.join(D,'m2code.bin'),'rb').read(); assert len(code)<=0x2000
    rom[BK_M2*0x2000:BK_M2*0x2000+len(code)]=code
    rom[BK_STR*0x2000:BK_STR*0x2000+len(strips)]=strips
    rom[BK_FIG*0x2000:BK_FIG*0x2000+len(m2figs)]=m2figs
out=os.path.join(D,'DoubleDragon_MSX2.rom' if MSX2 else 'DoubleDragon_ASCII8.rom'); open(out,'wb').write(rom)
print('ROM %s: %d KB, music banks from %d, data ends at %05X; resident: ROMLOAD=%04X RESBOOT=%04X end A=%04X B=%04X'%(out,romsize//1024,MUSBANK,off,S['ROMLOAD'],S['RESBOOT'],S['RES_A_END'],S['RES_B_END']),'HIGH ends %04X'%S2['HIGH_END'])
