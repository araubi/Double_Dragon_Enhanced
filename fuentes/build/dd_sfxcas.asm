; =============================================================================
;  Cinta: efectos de la recreativa con un solo golpe de envolvente (sin música ni
;  cuadros que los vayan cambiando). Ruido en el canal C, tono en el canal A (el
;  mezclador de la cinta es fijo: 9Eh) y los dos con la envolvente \___.
;  A = número del efecto (dd_sonido.asm). Página 0: tabla en 0040h, código en 0400h
;  (ceros de la ROM del Spectrum que la cinta no usa; cas_extra.asm los copia).
; =============================================================================
            ORG 0040h
            ;    ruido, periodo del tono (A), envolvente (byte alto; 1 = 36 ms)
CASTAB:     db 14 : dw 0      : db 03h          ; 00 puñetazo
            db 9  : dw 0      : db 04h          ; 01 patada
            db 28 : dw 1243   : db 0Dh          ; 02 derribado
            db 0  : dw 0      : db 0            ; 03
            db 31 : dw 1017   : db 14h          ; 04 bidón
            db 0  : dw 0      : db 0            ; 05
            db 0  : dw 430    : db 06h          ; 06 bate
            db 0,0,0,0, 0,0,0,0, 0,0,0,0        ; 07-09
            db 26 : dw 895    : db 0Ah          ; 0A roca
            db 31 : dw 1118   : db 18h          ; 0B piedras de la pared
            db 17 : dw 1598   : db 1Ch          ; 0C agua
            db 2  : dw 160    : db 05h          ; 0D latigazo
            db 0  : dw 0      : db 0            ; 0E
            db 4  : dw 0      : db 04h          ; 0F cuchillo
            db 1  : dw 140    : db 0Dh          ; 10 cuchillo parado
            db 0  : dw 127    : db 0Ch          ; 11 Linda
            db 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 ; 12-15
            db 20 : dw 932    : db 0Ch          ; 16 metralleta
            db 20 : dw 392    : db 18h          ; 17 jugador muriendo
            db 0  : dw 70     : db 04h          ; 18 zap (el de antes)
            db 24 : dw 523    : db 18h          ; 19 enemigo muriendo
CASTAB_N    EQU ($-CASTAB)/4
            ASSERT $ <= 00B0h

            ORG 0400h
CASSFX:     cp CASTAB_N
            ret nc
            add a,a
            add a,a
            ld l,a
            ld h,0
            ld de,CASTAB
            add hl,de
            ld a,(hl)               ; ruido
            ld c,6
            or a
            call nz,.w
            jr z,.v
            ld a,10h
.v:         ld c,10                 ; volumen C: envolvente o nada
            call .w
            inc hl
            ld e,(hl)
            inc hl
            ld d,(hl)
            ld a,e
            or d
            jr z,.t
            ld a,e
            ld c,0
            call .w
            ld a,d
            ld c,1
            call .w
            ld a,10h
.t:         ld c,8                  ; volumen A: envolvente o nada
            call .w
            inc hl
            ld a,(hl)
            ld c,12
            call .w
            xor a
            ld c,11
            call .w
            ld c,13                 ; forma \___ (y vuelve a empezar)
.w:         push af
            ld a,c
            out (PSGA),a
            pop af
            out (PSGW),a
            ret
            ASSERT $ <= 0482h
