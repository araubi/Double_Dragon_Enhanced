import sys,re
C={
0xC2D0:'Rutina de conmutación de slots (se copia a AFC8h para usarla con la pág.0 en RAM)',
0xC350:'ENTRADA BLOAD ,R: pone RAM en pág. 0,1,2 y reubica el cargador a 0556h',
0xDADC:'Detecta RAM en cada página probando escritura 20h/FAh vía ENASLT',
0xDB33:'Busca slot/subslot con RAM para la dirección HL (recorre 4x4 slots)',
0x0556:'Punto de entrada del cargador turbo (lo llama el juego para la multicarga)',
0x0559:'Secuencia de carga inicial: pantalla, código, misión 1, núcleo',
0x05A0:'Init Spectrum: SP=5B54h, IM 2 con I=E2h (vector -> 5B5Bh = RETI)',
0x05B3:'LOADER: IX=destino DE=longitud. Formato estilo Spectrum: flag + datos + XOR',
0x05BC:'Guarda FC8E-FCA5 en la pila y monta en FC9A un stub automodificable',
0x05E5:'L = valor PPI con pág.0 en BIOS, H = valor actual (RAM)',
0x0602:'Guarda byte en (IX); si cae en FC8E-FCA5 lo escribe en la copia salvada',
0x061E:'Bucle por byte: TAPIN, XOR checksum, borde VDP R#7 = contador (rayas)',
0x0631:'Fin: STMOTR off, restaura FC8E-FCA5, CP 1 -> Carry=error (no se comprueba)',
0x0667:'Init tape: PPI motor on, borde',
0x0676:'BLIT ZONA DE JUEGO: atributos buffer 2980h (20x32) -> tabla color VDP 2200h',
0x06C9:'Tabla tinta Spectrum (+bit7 brillo) -> byte color MSX (fondo negro fijo)',
0x06D9:'SETWRT propio: DE = dirección VRAM de escritura',
0x06E9:'Patrones buffer lineal 2C00h (20 filas x 256 bytes) -> VDP 0200h, outi desenrollado',
0x0A45:'HUD: filas 0-1 (4000h) y 22-23 (50C0h) de la pantalla Spectrum -> VDP',
0x0A70:'Copia 2 filas de caracteres Spectrum (entrelazado, inc h = línea) a patrones',
0x0AAD:'Hook: rellena 64 atributos con C y redibuja la pantalla Spectrum entera',
0x0BDC:'Convierte atributos Spectrum (tinta/papel/brillo) a color MSX x8 líneas',
0x0C45:'Paleta Spectrum normal -> MSX: 1,4,6,13,2,5,10,14',
0x0C4D:'Paleta Spectrum BRIGHT -> MSX: 1,4,8,9,3,7,11,15',
0x0C61:'MENÚ MSX (sustituye al CONTROL MENU original): fuente a FC00h, texto, logo',
0x0C7B:'Borra patrones (0000-17FF) y pone color 11h en toda la tabla de color',
0x0CF9:'Imprime cadena (códigos 16h=AT y,x  17h/18h=color  19h=sin color  FFh=fin)',
0x0D03:'Espera ESPACIO (fila 8 bit0) y salta a 9056h (inicio de misión)',
0x0D10:'Texto del menú en castellano',
0x0DA1:'JUGADOR 2: teclado O,P,Q,A,Espacio -> formato Kempston (000FUDLR)',
0x0DD4:'JUGADOR 1: joystick puerto A (PSG R#14) + cursores + RETURN; SHIFT->bit7',
0x0DD4+0:'',
0x0E5C:'Pinta un carácter de la fuente en FC00h directamente en VRAM',
0x1255:'Vuelca logo del menú: 500h patrones a VDP 1000h y 500h colores a 3000h',
0x126D:'LDIRVM propio: HL->VRAM DE, BC bytes',
0x9056:'INICIO DE MISIÓN (bloque de misión cargado en 9056-E14B)',
0x90F4:'BUCLE PRINCIPAL DEL JUEGO',
0x9158:'Pantalla de espera: HIT P1 FIRE TO BEGIN [OR CAPS TO LOAD MISSION n]',
0x91B2:'MULTICARGA: lee stub de 96h bytes en EA60h; byte 0 = nº de misión',
0x91E8:'Misión completada: fundido (sla del buffer) + COMPLETED MISSION',
0x9209:'GAME OVER',
0x9222:'Fundido: desplaza a la izquierda todo el buffer 2C00h 8 veces',
0x9257:'Retardo por bucle (sin interrupciones)',
0xE14C:'LECTURA DE CONTROLES: A = tipo; tabla de saltos en E167h',
0xE173:'Kempston (IN 1Fh) - original, inalcanzable en MSX',
0xE17A:'Fuller (IN 7Fh) - original, inalcanzable en MSX',
0xE18C:'Interface 2 -> PARCHEADO a 0DA1h (teclado jugador 2)',
0xE1A4:'Teclado Spectrum -> PARCHEADO a 0DD4h (joystick/cursores jugador 1)',
0xE612:'Hook "volcar pantalla": DI + JP 0676h',
0xE628:'Rutina Spectrum original de volcado (pila+LDI) - código muerto',
0xEA60:'Arranque del núcleo (después se sobrescribe con los stubs de misión)',
0xEA9C:'Punteros de la misión 1 (5B0B-5B1F) y salto a 9056h',
0xEADC:'Antes: CONTROL MENU Spectrum. Ahora salta al menú MSX 0C61h',
0xEAEF:'Restos del CONTROL MENU original (Kempston/Fuller/IF2/Cursor) - muerto',
0xECCC:'Rutina de beeper Spectrum (OUT FEh) - muerta; en MSX FEh es el mapper',
0xF027:'Restos de LD-BYTES Spectrum (CALL 0562h ROM) - muerto',
}
f,=sys.argv[1:]
for l in open(f):
    l=l.rstrip('\n')
    m=re.match(r'^  ([0-9A-F]{4})  ',l) or re.match(r'^L([0-9A-F]{4}):',l)
    if m:
        a=int(m.group(1),16)
        if a in C and C[a]:
            if l.startswith('L') or not any(True for _ in []):
                print('; ' + '-'*70); print('; %04Xh  %s'%(a,C[a])); C[a]=''
    print(l)
