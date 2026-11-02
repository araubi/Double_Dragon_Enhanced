# Uso (desde fuentes/emu): CBIOS_DIR=... python3 ../musica/capturar_psg.py ../build/DoubleDragon_ASCII8.rom 60 cap.pkl
"""Arranca la ROM en el emulador de pruebas y guarda los registros del PSG en cada cuadro."""
import sys,os,pickle
sys.path.insert(0,os.getcwd())
from rommachine import machine
rom=open(sys.argv[1],'rb').read(); secs=float(sys.argv[2]); out=sys.argv[3]
m=machine(rom,'A'); frames=[]; marks={}
def frame():
    f=m.L.emu_frames()
    while m.L.emu_frames()==f: m.run(2000)
    frames.append(bytes(m.psg()[:16]))
menu=False
while len(frames)<secs*50:
    frame()
    if not menu and m.get('pc') in range(0x0D03,0x0D10): pass
    if not menu and m.peek(0x02D0)==1 and 'start' not in marks: marks['start']=len(frames)
    if not menu and m.L.emu_exec_map()[0x0D03]:
        menu=True; marks['menu']=len(frames)
# pulsar ESPACIO y seguir 2 s para ver que se calla
m.key('SPACE'); 
for i in range(25): frame()
m.key('SPACE',False); marks['space']=len(frames)
for i in range(75): frame()
pickle.dump((frames,marks),open(out,'wb'))
print(marks,len(frames),'hz byte',hex(m.peek(0x2D1)),'st',m.peek(0x2D0))
