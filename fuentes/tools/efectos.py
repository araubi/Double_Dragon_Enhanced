"""Efectos de la recreativa imitados con un canal del PSG, cuadro a cuadro (1/60 s).
Cada cuadro: (volumen 0-15, frecuencia del tono en Hz o 0, periodo del ruido 1-31 o 0).
Diseñados a partir del análisis de las muestras (sfx/fit/show.py): duración, volumen
por cuadro, brillo (centroide), tono dominante."""
CLK = 1789772.5

def ramp(a, b, n):
    return [round(a + (b - a) * i / max(1, n - 1)) for i in range(n)]

def fr(vols, f=0, n=0):
    if not isinstance(f, list): f = [f] * len(vols)
    if not isinstance(n, list): n = [n] * len(vols)
    return [(v, ff, nn) for v, ff, nn in zip(vols, f, n)]

def sweep(a, b, k):
    return [a * (b / a) ** (i / max(1, k - 1)) for i in range(k)]

E = {}
# 00 puñetazo: golpe seco, un toque grave y ruido medio que se corta enseguida (~0,12 s;
#    Rubén, 2026-10-22: más secos y cortos)
E[0x00] = fr([15], 110, 20) + fr([15, 14, 12, 9, 6, 3], 0, 14)
# 01 patada: igual de seca, ruido más brillante (~0,15 s)
E[0x01] = fr([15], 170, 12) + fr([15, 15, 13, 11, 8, 5, 2], 0, 9)
# 02 derribado: golpe sordo contra el suelo y cola de ruido grave (~0,5 s)
E[0x02] = fr([15, 15, 15, 15, 14, 14], [100, 95, 90, 85, 80, 75], 31) + \
          fr(ramp(13, 2, 22), 0, [24] * 8 + [28] * 14)
# 04 bidón rebotando: botes graves (tono + ruido), cada vez más flojos y seguidos (~1,4 s)
def bote(v0, n, f=110):
    return fr([max(0, v0 - k) for k in (0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)][:n], f, 31)
E[0x04] = bote(15, 12) + fr([8, 7, 7, 6, 6, 7, 6, 5, 5, 6], 0, 31) + bote(14, 12, 120) + fr([6, 5, 5, 4, 4, 5], 0, 31) + \
          bote(13, 10, 125) + fr([5, 4, 4, 4], 0, 31) + bote(12, 9, 125) + fr([4, 3, 3], 0, 31) + bote(10, 8, 130)
# 06 esfuerzo con el bate: gruñido, tono que sube y luego baja (~0,25 s)
E[0x06] = fr([9, 12, 14, 15, 15, 15, 15, 15, 15, 14, 13, 11, 9, 6],
             sweep(250, 310, 6) + sweep(300, 140, 8))
# 0A roca rebotando: golpes secos más agudos que el bidón, tres botes (~0,9 s)
def golpe(v0, n, f=125, nz=26):
    return fr([max(0, v0 - 2 * k) for k in range(n)], f, nz)
E[0x0A] = golpe(15, 6) + fr([8, 7, 7, 6, 6, 6, 5, 5, 5, 4], 0, 28) + golpe(14, 6, 130) + fr([7, 6, 6, 5, 5, 4, 4, 3], 0, 28) + \
          golpe(15, 6, 128) + fr([7, 6, 5, 5, 4, 4], 0, 28) + golpe(12, 6, 250, 28)
# 0B piedras de la pared: retumbo grave sostenido (~0,85 s)
E[0x0B] = fr([12, 13, 14, 14, 15, 15, 14, 15, 15, 14] * 4 + ramp(14, 4, 11),
             [100, 96, 92, 100, 104, 98, 94, 100, 106, 98] * 4 + [96] * 11,
             ([31, 0, 0, 31, 0] * 11)[:51])
# 0C caída al agua: zambullida grave y chapoteo de ruido largo (~1 s)
E[0x0C] = fr([15, 15, 14, 13], [80, 75, 70, 65], 31) + fr(ramp(9, 6, 12), 55, 31) + \
          fr([12, 14, 15, 15, 15, 14] + ramp(14, 9, 30) + ramp(9, 2, 8), 0, [18, 16, 15] + [17] * 41)
# 0D latigazo: chasquido muy agudo y cola con tono (~0,3 s)
E[0x0D] = fr([15, 15], 0, [2, 4]) + fr([15, 14, 14, 13, 12, 11, 10, 9, 7, 5, 3], [720, 700, 680, 560, 560, 450, 440, 430, 420, 410, 400], 12)
# 0F lanzar cuchillo: chasquido corto y brillante (~0,2 s)
E[0x0F] = fr([15, 15, 14, 13, 11, 8, 6, 5, 4, 3, 2], 0, [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20])
# 10 parar un cuchillo de una patada: golpe metálico que resuena (~0,6 s)
E[0x10] = fr([15, 15], 0, 1) + fr([15, 15, 14, 14, 14, 14], 800, 2) + \
          fr(ramp(14, 4, 26), 0, [1, 2] * 13)
# 11 Linda muriendo: grito agudo con vibrato que se quiebra (~0,4 s)
E[0x11] = fr([9, 12, 14], [700, 800, 880]) + \
          fr([15] * 11, [880 * (1.03 if i % 4 < 2 else 0.97) for i in range(11)]) + \
          fr([14, 14, 13, 13, 12], [520, 500, 490, 480, 470]) + fr([10, 8, 6, 3], [440, 420, 400, 380])
# 16 metralleta: ráfaga de disparos graves (~0,9 s)
def tiro(v0):
    return fr([v0, v0 - 1, v0 - 3, v0 - 6, v0 - 9], [120, 110, 0, 0, 0], [20, 22, 24, 26, 28])
E[0x16] = fr([12, 13], 60, 31) + sum((tiro(15 if k % 2 == 0 else 14) for k in range(9)), []) + fr(ramp(8, 2, 6), 0, 30)
# 17 jugador muriendo: quejido corto y lamento largo que baja (~1,3 s)
E[0x17] = fr([13, 15], 290, 20) + fr([15, 15, 15, 15, 14, 13, 11, 9, 7], 285) + fr([0] * 12) + \
          fr(ramp(9, 13, 6) + [13] * 14 + ramp(12, 3, 26), sweep(275, 185, 46))

# 18 el "zap" del final del juego (el efecto que ya tenía la conversión)
E[0x18] = fr([15, 14, 12, 10, 8, 6, 4, 2, 1], 1598)

# 19 enemigo muriendo: el del jugador, más grave (Rubén, 2026-10-22)
E[0x19] = [(v, f * 0.7, n) for v, f, n in E[0x17]]

ORDEN = [0x00, 0x01, 0x02, 0x04, 0x06, 0x0A, 0x0B, 0x0C, 0x0D, 0x0F, 0x10, 0x11, 0x16, 0x17, 0x19]

def tp(f):
    return min(4095, round(CLK / 16 / f)) if f else 0

def pasos(e):
    """[(vol, tp, np)] por cuadro"""
    return [(v, tp(f), n) for v, f, n in e]

def codificar(e):
    """bytes: byte0 = vol | 10h ruido | 20h tono | (repeticiones-1)<<6; luego ruido, tono (2)"""
    st = pasos(e); out = bytearray(); i = 0
    while i < len(st):
        k = 1
        while k < 4 and i + k < len(st) and st[i + k] == st[i]: k += 1
        v, t, n = st[i]
        if not t and not n: v = 0
        out.append(v | (0x10 if n else 0) | (0x20 if t else 0) | ((k - 1) << 6))
        if n: out.append(n)
        if t: out += bytes([t & 255, t >> 8])
        i += k
    out.append(0xFF)
    return bytes(out)

def inc(path):
    """sfx_data.inc para mus_player.asm"""
    n = max(E) + 1
    out = ['; generado por efectos.py: efectos de la recreativa, un paso por cuadro de vídeo',
           'SFX_N       EQU %d' % n, 'SFXTAB:']
    out += ['            dw %s' % ('SFX_%02X' % i if i in E else '0') for i in range(n)]
    for i in sorted(E):
        b = codificar(E[i])
        out.append('SFX_%02X:' % i)
        for k in range(0, len(b), 16):
            out.append('            db ' + ','.join('%d' % x for x in b[k:k + 16]))
    open(path, 'w').write('\n'.join(out) + '\n')

if __name__ == '__main__':
    import sys
    inc(sys.argv[1])
