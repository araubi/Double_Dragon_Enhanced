; =============================================================================
;  Dibujo de figuras más rápido (solo ROM; parches por patrón en build_rom.py).
;  La rutina de figuras de cada misión pinta cada línea de una figura byte a
;  byte con una llamada por byte (BDA0h/BD90h en la 3A) y comprobando el borde
;  derecho en cada uno. En 3A y 3B hay el doble de figura que en la misión 1 y
;  ese bucle es lo que más tiempo se lleva. Ahora la línea entera se pinta aquí:
;  si cabe en pantalla, sin comprobaciones; si no, byte a byte como el original.
;  Entrada: B = ancho en bytes, C = columna (20h o más: fuera por la izquierda),
;  HL = origen (máscara, dibujo) x B, DE = destino. Salida: HL += 2*B, DE += los
;  bytes pintados (lo mismo que el bucle original).
;  El volteo horizontal (tabla de bits al revés en E512h) usa una copia alineada.
; =============================================================================
; con máscara: pantalla AND máscara OR dibujo
DRAWM:      ld a,c
            cp 20h
            jr nc,.s
            add a,b
            cp 21h
            jr nc,.s
.l:         ld a,(de)
            and (hl)
            inc hl
            or (hl)
            ld (de),a
            inc hl
            inc de
            djnz .l
            ret
.s:         ld a,c
            cp 20h
            jr nc,.k
            ld a,(de)
            and (hl)
            inc hl
            or (hl)
            ld (de),a
            inc de
            jr .n
.k:         inc hl
.n:         inc hl
            inc c
            djnz .s
            ret
; sin máscara (BD90h): donde el primer byte tiene un 1 queda la pantalla y
; donde tiene un 0, el segundo byte invertido
DRAWI:      ld a,c
            cp 20h
            jr nc,.s
            add a,b
            cp 21h
            jr nc,.s
.l:         inc hl
            ld a,(de)
            xor (hl)
            cpl
            dec hl
            and (hl)
            inc hl
            xor (hl)
            cpl
            ld (de),a
            inc hl
            inc de
            djnz .l
            ret
.s:         ld a,c
            cp 20h
            jr nc,.k
            inc hl
            ld a,(de)
            xor (hl)
            cpl
            dec hl
            and (hl)
            inc hl
            xor (hl)
            cpl
            ld (de),a
            inc de
            jr .n
.k:         inc hl
.n:         inc hl
            inc c
            djnz .s
            ret
; volteo: A bytes desde DE
FLIP:       ld b,a
            ld h,high FLIPTAB
.l:         ld a,(de)
            ld l,a
            ld a,(hl)
            ld (de),a
            inc de
            djnz .l
            ret
; ---- sprites de los jugadores (dd_sprites.asm): lo que cabe en este hueco
SPROFF:     push af
            push hl
            ld hl,1B00h
            call VWR
            ld a,0D0h
            out (98h),a
            ld a,36h                ; atributos en 1B00h
            out (99h),a
            ld (DISP),a
            ld a,85h
            out (99h),a
            xor a
            ld (ACT),a
            ld (R5P),a
            pop hl
            pop af
            ret
SPRAAD:     call SPROFF
            jp AADHOOK
SPRFRM:     call SPRUPD
            jp FRAME5B
SPRFADE:    call SPROFF
            push af
            ld a,1
            ld (FULLF),a
            pop af
            ld hl,2C00h
            ret
; 16 bytes de una columna de sprite a la VRAM; C |= cada uno (dd_sprites.asm)
SPCOL:      push hl
            ld b,4
.cl:        DUP 4
            ld a,(hl)               ; 7
            out (98h),a             ; 11
            or c                    ; 4
            ld c,a                  ; 4
            inc l                   ; 4 -> 30 T
            EDUP
            djnz .cl
            pop hl
            ret
            ASSERT $ <= 0FB00h
            ALIGN 256
FLIPTAB:    INCLUDE "fliptab.inc"   ; copia de la tabla de E512h (generada)
