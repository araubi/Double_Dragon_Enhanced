# Uso (desde fuentes/emu): CBIOS_DIR=... python3 ../musica/muestras.py ../build/DoubleDragon_ASCII8.rom salida_dir [MB_xx ...]
"""Graba cada canción tal como la toca el reproductor de la ROM (desde el menú, 60 Hz) y la
pasa a WAV: una vuelta entera más unos segundos para oír el punto de bucle."""
import sys,os,pickle,subprocess
sys.path.insert(0,os.getcwd())
from rommachine import machine
rom=open(sys.argv[1],'rb').read(); od=sys.argv[2]
MB={l.split()[0]:int(l.split()[2]) for l in open('../build/musbanks.inc')}
DUR={'MB_02':92,'MB_06':63,'MB_07':94,'MB_08':42,'MB_09':38,'MB_04':6,'MB_03':26}
if len(sys.argv)>3: DUR={k:v for k,v in DUR.items() if k in sys.argv[3:]}   # solo esas
NAME={'MB_02':'02_slums_misiones_1_y_4','MB_06':'06_industrial_misiones_2_y_5A','MB_07':'07_woods_misiones_3A_y_3B',
      'MB_08':'08_enemy_hq_mision_5B','MB_09':'09_final_tras_willy','MB_04':'04_mission_complete',
      'MB_03':'03_entrada_de_abobo_mision_1'}
m=machine(rom,'A')
f=m.L.emu_frames()
while not m.L.emu_exec_map()[0x0D03]: m.run(100000)
for k,secs in DUR.items():
    m.poke(0x2F0,MB[k]); m.poke(0x2D0,0)
    frames=[]
    while len(frames)<secs*60:
        f=m.L.emu_frames()
        while m.L.emu_frames()==f: m.run(2000)
        frames.append(bytes(m.psg()[:16]))
    pk=os.path.join(od,NAME[k]+'.pkl'); pickle.dump((frames,{}),open(pk,'wb'))
    wav=pk[:-4]+'.wav'
    subprocess.run([sys.executable,os.path.join(os.path.dirname(os.path.abspath(__file__)),'psg2wav.py'),pk,wav,'0',str(len(frames)),'60'],check=True)
    os.remove(pk); print(k,wav)
