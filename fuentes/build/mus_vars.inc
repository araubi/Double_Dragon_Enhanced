; variables de la música de presentación: página 0, 02D0-02F1 (ceros que el juego
; no usa; 0000-0037 no vale: el juego hace CALL 0000h y lo recorre como NOPs)
MUS_ST      EQU 02D0h       ; 0 = arrancar canción, 1 = sonando, 2 = parada
MUS_HZ      EQU 02D1h       ; bit 7 del byte 002Bh de la BIOS: 1 = 50 Hz
MUS_SP      EQU 02D2h       ; 2: pila del llamante mientras suena la música
MUS_ACC     EQU 02D4h       ; 2: acumulador de semicorcheas (16 bits)
MUS_MIX     EQU 02D6h       ; mezclador calculado en este cuadro
MUS_V       EQU 02D8h       ; 4 voces x 6: ptr(2), cnt, nota, inst, cuadro (hasta 02EFh)
MSTACK      EQU 2940h       ; pila propia (2900-297F no lo usa el juego; LSTACK = 2980h)
; música de las misiones (solo ROM): 02F0-02F7
MUS_BK      EQU 02F0h       ; banco de la canción que suena (reproductor + datos)
MUS_MIS     EQU 02F1h       ; misión cuya música suena (0 = ninguna: se elige al jugar)
MUS_SFX     EQU 02F2h       ; cuadros que el canal C es de un efecto de sonido
MUS_PEND    EQU 02F3h       ; misión cargada cuya canción empieza en el primer cuadro de juego (0 = ninguna)
MUS_CNT     EQU 02F4h       ; 2: contador de cuadros de las esperas
MUS_ABO     EQU 02F6h       ; 1: bit 7 = ya suena la música de jefe (FRAMEHK)
; efectos de sonido de la ROM (mus_player.asm): 02F8-02FB
SFX_REQ     EQU 02F8h       ; efecto pedido + 1 (0 = ninguno)
SFX_PTR     EQU 02F9h       ; 2: siguiente paso del efecto que suena (MUS_SFX = 1 mientras suena)
SFX_HOLD    EQU 02FBh       ; cuadros que aún dura el paso actual
