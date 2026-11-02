; =============================================================================
;  Látigo: en la recreativa solo Linda lo recoge del suelo. En la conversión,
;  cualquier enemigo podía cogerlo. La rutina de recoger objetos de cada misión
;  (la que pone el objeto en (ix+7) del que lo coge) mira cada objeto cercano con
;  una llamada a "LD A,(IX+7) / AND A / RET" (NZ: ya lo lleva alguien); esa llamada
;  pasa a WHIPCHK (parche por patrón en build_ram.py).
;  Objeto: +9 = clase (nibble alto del tipo del registro - 1); el látigo es la 1
;  (solo lo traen las Lindas, registros 22h). Recogen el látigo los jugadores y
;  Linda (tipo 2); Jeff (tipo 0 en un hueco de enemigo) y los demás no.
; =============================================================================
            ORG 0CABh               ; resto de la antigua rutina de borrado de VRAM
WHIPCHK:    ld a,(ix+7)             ; IX = objeto
            or a
            ret nz                  ; ya lo lleva alguien
            ld a,(ix+9)
            dec a
            jr nz,.si               ; no es el látigo
            push hl
            ld hl,8                 ; pila: HL, retorno, DE, BC, IX del que lo coge
            add hl,sp
            ld e,(hl)
            inc hl
            ld d,(hl)               ; DE = estructura del que lo coge (el llamante
            pop hl                  ; recupera DE de la pila al volver)
            call ISPLAYER_DE
            ret z                   ; jugador: sí
            push hl
            ld hl,15
            add hl,de
            ld a,(hl)
            pop hl
            and 0Fh
            cp 2                    ; Linda: Z, sí; los demás: NZ, no
            ret
.si:        xor a
            ret

; Agarrar de los pelos (rutina de golpes de cada misión): el agarrado tenía que
; ser de tipo 0 o 1 ("LD A,(IY+15) / CP 2 / JR NC,no"); Jeff es tipo 0 en un
; hueco de enemigo y también se podía agarrar. La llamada devuelve el mismo
; acarreo que ese CP 2, pero con Jeff como si fuera tipo 2 (no se agarra).
GRABCHK:    call ISPY               ; Z: jugador; A = tipo
            jr z,.c
            or a
            jr nz,.c
            ld a,2                  ; Jeff
.c:         cp 2
            ret
WHIPCHK_END:
            ASSERT $ <= 0CF9h
