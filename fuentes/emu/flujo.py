# Uso: CBIOS_DIR=... python3 flujo.py ../build/DoubleDragon_ASCII8.rom [A|B|C]
"""Prueba del flujo nuevo: menú -> ESPACIO -> título -> ESPACIO -> misión; al completar cada misión
se carga la siguiente sola. Comprueba también las teclas de los dos jugadores."""
import sys,os,random
sys.path.insert(0,os.getcwd())
import romtest, coverage as C, msx
from rommachine import machine
msx.KEYS.update({'W':(5,4),'S':(5,0),'D':(3,1),'RET':(7,7)})
rom=open(sys.argv[1],'rb').read(); lay=sys.argv[2] if len(sys.argv)>2 else 'A'
P2=0x0DA1   # P2KEYS (dd_controles.asm)
m=machine(rom,lay); m.det_r(True,1); g=romtest.G(m); rnd=random.Random(3)
assert g.run_until([0x0D03],600_000_000)==0x0D03
# teclas: llamar a P2KEYS y al lector del jugador 1 (E1A4) con cada tecla
def call(addr,c=0):
    sv={r:m.get(r) for r in ('pc','sp','bc')}
    sp=0x2900; m.poke(sp,0x03); m.poke(sp+1,0x0D)      # vuelve a 0D03
    m.set('sp',sp); m.set('bc',c); m.set('pc',addr)
    assert m.run_until([0x0D03],1_000_000)
    a=m.get('af')>>8
    m.set('sp',sv['sp']); m.set('bc',sv['bc']); m.set('pc',sv['pc'])
    return a
for k,exp in (('W',8),('S',4),('A',2),('D',1),('SHIFT',16)):
    m.key(k); v=call(P2); m.key(k,False); print('J2',k,v,'ok' if v&31==exp else 'MAL')
for k,exp in (('UP',8),('DOWN',4),('LEFT',2),('RIGHT',1),('SPACE',16),('RET',0)):
    m.key(k); v=call(0xE1A4); m.key(k,False); print('J1',k,v&31,'ok' if v&31==exp else 'MAL')
m.screenshot('shots/menu_nuevo.png',1)
m.key('SPACE'); m.run(3_000_000); m.key('SPACE',False)
assert g.run_until([C.TITLE[1]])==C.TITLE[1]
m.key('SPACE'); assert g.run_until([C.FRAME])==C.FRAME; m.key('SPACE',False)
res=[]
for mission in range(1,7):
    romtest.play(g,60,rnd); m.release_all()
    chk,flag=C.CHECK[mission]
    assert g.run_until([chk])==chk; m.poke(flag,1)
    nxt=mission+1
    if nxt in C.TITLE:
        pc=g.run_until([C.TITLE[nxt]],600_000_000)
    else:
        pc=g.run_until([0x9056],600_000_000); m.run(20_000_000)
    diff=romtest.ram_ok(m,nxt) if pc else None
    m.screenshot('shots/titulo_m%d.png'%nxt,1)
    res.append((nxt,'llega' if pc else 'NO',diff,'5B1B=%d'%m.peek(0x5B1B)))
    if not pc: break
    m.key('SPACE'); assert g.run_until([C.FRAME],400_000_000)==C.FRAME; m.key('SPACE',False)
print(lay,res)
