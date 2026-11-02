# Uso: CBIOS_DIR=... python3 latigo.py ../build/DoubleDragon_ASCII8.rom
# Llama a la rutina de recoger objetos de la misión 1 (A715h) con un objeto en el suelo
# al lado: el látigo solo lo cogen Linda y los jugadores; las otras armas, cualquiera.
import sys,os
sys.path.insert(0,os.getcwd())
import romtest, coverage as C
from rommachine import machine
rom=open(sys.argv[1],'rb').read()
m=machine(rom,'A'); m.det_r(True,1); g=romtest.G(m)
assert g.run_until([0x0D03],600_000_000)==0x0D03
m.key('SPACE'); m.run(3_000_000); m.key('SPACE',False)
assert g.run_until([C.TITLE[1]])==C.TITLE[1]; m.run(3_000_000)
m.key('SPACE'); assert g.run_until([C.FRAME])==C.FRAME; m.key('SPACE',False)
for k in range(30): m.run(1); assert g.run_until([C.FRAME])==C.FRAME
p1=m.peekw(0x1C92); obj=p1+18*5; ok=True
snap=bytes(m.peek(a) for a in range(0x8000,0x10000)); regs={r:m.get(r) for r in ('sp','pc','ix','iy','af','bc','de','hl')}
def prueba(quien,slot,tipo,clase,espera):
    global ok
    for i,v in enumerate(snap): m.poke(0x8000+i,v)
    for r,v in regs.items(): m.set(r,v)
    act=p1+18*slot
    if slot>=2:
        for i,v in enumerate(bytes.fromhex('05030714 0a 09af000000000000040003000050'.replace(' ',''))): m.poke(act+i,v)
        m.poke(act+15,tipo)
    m.poke(act+7,0); X,Y=m.peek(act+3),m.peek(act+4)
    for i in range(18): m.poke(obj+i,0)
    for i,v in enumerate(bytes.fromhex('0502041 50b10af0000'.replace(' ',''))): m.poke(obj+i,v)
    m.poke(obj+3,X); m.poke(obj+4,Y+3); m.poke(obj+7,0); m.poke(obj+9,clase)
    m.poke(0xB7BE,1)
    sp=m.get('sp')-2; m.poke(sp,C.FRAME&255); m.poke(sp+1,C.FRAME>>8); m.set('sp',sp)
    m.set('ix',act); m.set('pc',0xA715)
    assert g.run_until([C.FRAME])==C.FRAME
    coge=m.peek(act+7)!=0
    r=coge==espera; ok&=r
    print('%-28s %-8s %s'%(quien,'lo coge' if coge else 'no',  'ok' if r else 'MAL'))
prueba('jugador 1 / látigo',0,0,1,True)
prueba('Linda / látigo',2,0x22,1,True)
prueba('enemigo normal / látigo',2,0x11,1,False)
prueba('Abobo / látigo',2,0x03,1,False)
prueba('Jeff / látigo',2,0x00,1,False)
prueba('enemigo normal / cuchillo',2,0x11,2,True)
print('TODO BIEN' if ok else 'HAY FALLOS')
