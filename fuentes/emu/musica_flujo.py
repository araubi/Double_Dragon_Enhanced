# Uso: CBIOS_DIR=... python3 musica_flujo.py ../build/DoubleDragon_ASCII8.rom [A|B|C]
"""Prueba de la música por misión: silencio en cada pantalla de título (pulsar botón), canción al jugar, 'Mission Complete' al acabar
cada misión, silencio en GAME OVER, final tras Willy (forzado) y vuelta al menú."""
import sys,os,random,re
sys.path.insert(0,os.getcwd())
import romtest, coverage as C
from rommachine import machine
B='../build'; S={}
for line in open(B+'/dd_rom.sym'):
    mm=re.match(r'(\S+):\s+EQU\s+0x([0-9A-Fa-f]+)',line)
    if mm: S[mm.group(1)]=int(mm.group(2),16)
MB={l.split()[0]:int(l.split()[2]) for l in open(B+'/musbanks.inc')}
NAME={v:k for k,v in MB.items()}
rom=open(sys.argv[1],'rb').read(); lay=sys.argv[2] if len(sys.argv)>2 else 'A'
m=machine(rom,lay); m.det_r(True,1); g=romtest.G(m); rnd=random.Random(3)
ok=True
def st(): return '%s/%d'%(NAME.get(m.peek(0x2F0),'?'),m.peek(0x2D0))
def silencio(what):
    global ok
    p=m.psg(); r=m.peek(0x2D0)==2 and p[8]==0 and p[9]==0 and p[10]==0
    ok&=r; print('%-34s %-10s %s'%(what,'ST=%d'%m.peek(0x2D0),'ok (silencio)' if r else 'MAL (suena)'))
def check(what,exp_bank,exp_st=1):
    global ok
    r=(NAME.get(m.peek(0x2F0))==exp_bank) and m.peek(0x2D0)==exp_st
    ok&=r; print('%-34s %-10s %s'%(what,st(),'ok' if r else 'MAL (esperado %s/%d)'%(exp_bank,exp_st)))
assert g.run_until([0x0D03],600_000_000)==0x0D03
m.run(5_000_000); check('menú','MB_01')
m.key('SPACE'); m.run(3_000_000); m.key('SPACE',False)
assert g.run_until([C.TITLE[1]])==C.TITLE[1]; m.run(3_000_000)
SONG={1:'MB_02',2:'MB_06',3:'MB_07',4:'MB_07',5:'MB_02',6:'MB_06',7:'MB_08'}
silencio('título misión 1')
m.key('SPACE'); assert g.run_until([C.FRAME])==C.FRAME; m.key('SPACE',False)
JEFE={1:(3,112,103,'MB_03','último Abobo'),2:(0,131,None,'MB_03','Jeff'),
      4:(3,140,112,'MB_03','Abobos del final'),5:(3,150,None,'MB_03','Abobo de la 4')}
def jefe(mission):  # figura del tipo del jefe: si esperaba con otra energía no cambia; con la suya sí, aunque le peguen al salir
    if mission not in JEFE: return
    typ,en,otra,song,txt=JEFE[mission]
    assert g.run_until([C.FRAME])==C.FRAME
    p1=m.peekw(0x1C92); slot=p1+36+18*2
    m.poke(slot,0); romtest.play(g,2,rnd); m.release_all()
    if otra is not None:
        m.poke(slot+15,typ); m.poke(slot+17,otra); romtest.play(g,2,rnd)     # espera con otra energía
        m.poke(slot,5); m.poke(slot+9,0)
        romtest.play(g,3,rnd); m.release_all(); check('otro de su tipo (misión %d)'%mission,SONG[mission])
        if otra>en:     # pierde energía y pasa por la del jefe: no debe cambiar
            for e in (en+2,en,en-2):
                m.poke(slot+17,e); romtest.play(g,2,rnd)
            m.release_all(); check('  ...y baja su energía (misión %d)'%mission,SONG[mission])
        m.poke(slot+9,0xFF); m.poke(slot+8,0x10); m.poke(slot+17,0)     # se le quita del juego
        for k in range(40):
            romtest.play(g,1,rnd)
            if os.environ.get('DBGJ'): print('  k',k,' '.join('%02X'%m.peek(slot+i) for i in range(18)),'%02X'%m.peek(0x2F6))
            if m.peek(slot)==0: break
        m.release_all()
    m.poke(slot+15,typ); m.poke(slot+17,en); romtest.play(g,2,rnd)          # espera con la del jefe
    m.poke(slot,5); m.poke(slot+9,0); m.poke(slot+17,en//4)                 # y le pegan nada más salir
    for k in range(3):
        romtest.play(g,1,rnd)
        if os.environ.get('DBGJ'): print('   ',' '.join('%02X'%m.peek(slot+i) for i in range(18)),'%02X'%m.peek(0x2F6))
    m.release_all(); check('aparece %s (misión %d)'%(txt,mission),song)
    m.poke(slot,0)
for mission in range(1,7):
    romtest.play(g,40,rnd); m.release_all()
    check('jugando misión %d'%mission,SONG[mission])
    jefe(mission)
    chk,flag=C.CHECK[mission]; assert g.run_until([chk])==chk; m.poke(flag,1)
    assert g.run_until([S['MCOMPL']],300_000_000); m.run(8_000_000)    # COMPLETED MISSION
    check('MISSION COMPLETE %d'%mission,'MB_04')
    nxt=mission+1
    if nxt in C.TITLE:
        assert g.run_until([C.TITLE[nxt]],600_000_000); m.run(3_000_000); silencio('título misión %d'%nxt)
    else:
        assert g.run_until([0x9056],600_000_000); m.run(20_000_000); silencio('título misión 7')
    m.key('SPACE'); assert g.run_until([C.FRAME],400_000_000)==C.FRAME; m.key('SPACE',False)
romtest.play(g,40,rnd); m.release_all(); check('jugando misión 7',SONG[7])
# 5B: la del menú al llegar el scroll (C40Eh) a la escalera (SC_5B), no con Willy
m.poke(0xC40E,0x13); romtest.play(g,3,rnd); m.release_all(); check('antes de la escalera (5B)',SONG[7])
m.poke(0xC40E,0x14); romtest.play(g,3,rnd); m.release_all(); check('en la escalera (5B)','MB_01')
# GAME OVER: sin créditos ni vidas
m.key('SPACE'); assert g.run_until([C.FRAME],400_000_000)==C.FRAME; m.key('SPACE',False)
romtest.play(g,10,rnd); m.release_all()
assert g.run_until([C.FRAME])==C.FRAME
m.ret(); m.set('pc',0x92D8)          # GAME OVER de la misión 5B
assert g.run_until([S['GOVER']],100_000_000); m.run(2_000_000)
p=m.psg(); r=m.peek(0x2D0)==2 and p[8]==0 and p[9]==0
print('%-34s ST=%d vol %d %d %d %s'%('GAME OVER',m.peek(0x2D0),p[8],p[9],p[10],'ok' if r else 'MAL')); ok&=r
assert g.run_until([0x9084],300_000_000); m.run(5_000_000); check('sigue la 7 tras la escalera (créditos)','MB_01')   # la partida sigue donde estaba
# GAME OVER sin créditos
m.key('SPACE'); assert g.run_until([C.FRAME],400_000_000)==C.FRAME; m.key('SPACE',False)
romtest.play(g,5,rnd); m.release_all()
assert g.run_until([C.FRAME])==C.FRAME; m.poke(0x5B08,0); m.ret(); m.set('pc',0x92D8)
assert g.run_until([S['GOVER']],100_000_000); m.run(2_000_000); print('%-34s ST=%d'%('GAME OVER sin créditos',m.peek(0x2D0)))
r=g.run_until([0x0D03],900_000_000); m.run(5_000_000); print('  vuelve al menú:', 'sí' if r else 'NO (pc %04X)'%m.get('pc')); check('menú tras GAME OVER','MB_01')
# final forzado (al final de todo, porque luego la partida vuelve a empezar): otra partida
# hasta la 5B, volver del volcado al bucle principal y saltar a "Willy derrotado" (91D5h)
romtest.boot(g)
for k in range(1,7): romtest.next_mission(g,k)
assert g.run_until([C.FRAME])==C.FRAME; m.ret(); m.set('pc',0x91D5)
assert g.run_until([S['ENDWAIT']],100_000_000); m.run(10_000_000); check('final (Willy derrotado)','MB_09')
f0=m.frames; m.run(3579545*6)
m.key('SPACE'); r=g.run_until([S['ENDLOGO']],3579545*3); m.key('SPACE',False)
print('  el final dura %.1f s y sale con el disparo: %s'%((m.frames-f0)/60,'sí' if r else 'NO')); ok&=bool(r)
m.run(3579545)
logo=open(B+'/logo_sc2.bin','rb').read(); v=bytes(m.vram)
r=v[0:0x1800]==logo[:0x1800] and v[0x2000:0x3800]==logo[0x1800:] and all(v[0x1800+i]==i%256 for i in range(768)) and v[0x1B00]==0xD0
m.screenshot('logo_final.png',2)
print('%-34s %-10s %s'%('logo tras el final',st(),'ok' if r else 'MAL')); ok&=r; check('  ...con la música del final','MB_09')
r=g.run_until([0x0D03],900_000_000); m.run(5_000_000); print('  vuelve al menú:', 'sí' if r else 'NO (pc %04X)'%m.get('pc')); ok&=bool(r)
check('menú tras el final','MB_01')
print('TODO BIEN' if ok else 'HAY FALLOS')
