; =============================================================================
;  Controles por defecto del proyecto (Rubén, 2026-10-21):
;   jugador 1: cursores + ESPACIO (o joystick 1, como antes)
;   jugador 2: W, A, S, D + SHIFT        (antes O, P, Q, A + ESPACIO)
;  El juego recibe bits 0 derecha, 1 izquierda, 2 abajo, 3 arriba, 4 disparo.
;  Compartido por la ROM y la cinta.
; =============================================================================

; --- jugador 1 (0E09h-0E5Bh, lectura de teclado tras el joystick): disparo
;     RETURN (fila 7 bit 7) -> ESPACIO (fila 8 bit 0)
            ORG 0E4Dh
            db 0F8h                 ; ld a,0F8h (era 0F7h)
            ORG 0E52h
            rra                     ; bit 0 (era rla, bit 7)

; --- jugador 2: se reescribe en su sitio el lector de teclado (tipo 4, lo llama E18Ch).
;     Entrada: C = bits 5-7 del lector del jugador 1. Salida: A.
;     Ocupa 0DA1-0DCEh y sigue en 0DD7h (0DD4h es el salto a JOYFIX; 0DD7-0DE5h estaba muerto).
            ORG 0DA1h
P2KEYS:     ld b,c
            ld a,0F5h               ; fila 5: Z Y X W V U T S
            out (0AAh),a
            in a,(0A9h)
            bit 4,a
            jr nz,.s
            set 3,b                 ; W arriba
.s:         bit 0,a
            jr nz,.a
            set 2,b                 ; S abajo
.a:         ld a,0F2h               ; fila 2: B A ...
            out (0AAh),a
            in a,(0A9h)
            bit 6,a
            jr nz,.d
            set 1,b                 ; A izquierda
.d:         ld a,0F3h               ; fila 3: J I H G F E D C
            out (0AAh),a
            in a,(0A9h)
            bit 1,a
            jr nz,.f
            set 0,b                 ; D derecha
.f:         jr P2KEYS2
            ASSERT $ <= 0DD4h
            ORG 0DD7h
P2KEYS2:    ld a,0F6h               ; fila 6: ... SHIFT
            out (0AAh),a
            in a,(0A9h)
            rra
            jr c,.x
            set 4,b                 ; SHIFT disparo
.x:         ld a,b
            ret
            ASSERT $ <= 0DE6h       ; 0DE6h: decodificación del joystick (JOYFIX)

; --- textos del menú de opciones (mismo formato: 16h fila col, 18h + 8 colores)
            ORG 0D10h
            db 16h,4,8, 18h,81h,0A1h,0B1h,31h,0B1h,0A1h,51h,51h
            db "OPCIONES MENU:"
            db 16h,7,3, 18h,0F1h,0A1h,0F1h,0B1h,0F1h,31h,0F1h,0F1h
            db "JUG.1=JOY O CURSORES+ESPACIO"
            db 16h,9,3, 18h,0F1h,0A1h,0F1h,0B1h,0F1h,31h,0F1h,0F1h
            db "JUG.2=W,A,S,D + SHIFT"
            db 16h,12,3, 18h,0D1h,0D1h,0A1h,0A1h,21h,21h,0C1h,0C1h
            db "PULSA ESPACIO PARA JUGAR"
            db 0FFh
            ASSERT $ <= 0D9Bh

; --- menú: ESPACIO empieza la partida y también es el disparo del jugador 1, así que se
;     espera a que se suelte; si no, la pantalla "HIT P1 FIRE TO BEGIN" se saltaría sola.
;     (la ROM sustituye esta llamada por MUSOFF, que hace lo mismo y además calla la música)
            ORG 0D9Bh
            call SPCREL
            ORG 1DA8h               ; hueco de la página de sombra del marcador (bytes bajos
                                    ; 40h-BFh libres; scrollrec8 acaba en 1D9Fh). La cinta
                                    ; también lo copia (p0d en build_cas.py).
SPCREL:     ld a,0F8h
            out (0AAh),a
            in a,(0A9h)
            rra
            jr nc,SPCREL
            jp 0C7Bh
; ---- misión 5A: cada piedra se repintaba entera (5x5 casillas) en cada cuadro aunque no
;      cambiara; ahora solo cuando cambia su fase (contador 1-6). En lugar de «call B19Ch».
STDR:       ld a,(STC)
            dec a
            cp 6
            ret nc
            jp 0B19Ch
STC:        db 0
            ASSERT $ <= 1DC0h
