; =============================================================================
;  Reproductor PSG de las músicas (MegaROM, un banco de 8 KB por canción con su
;  copia del reproductor). Se ejecuta en 4000h con la página 1 apuntando al
;  cartucho (lo llama MUSFRM, en la página 0). Variables en la página 0 (02D0h-).
;  Música: "Double Dragon" (Technos Japan, 1987), compuesta por Kazunaka Yamane;
;  arreglos a 3 voces PSG desde los VGM de la recreativa (vgm2psg.py, arreglos.py).
;  mus_cur.inc (lo escribe build_rom.py) trae STEP50/STEP60 y los datos.
;  Mientras MUS_SFX > 0 el canal C es de un efecto del juego: no se toca. Los efectos
;  (los de la recreativa imitados cuadro a cuadro) los toca SFXSTEP, al final del fichero.
;  WAH (03, entrada de Abobo): en la recreativa la melodía sube de volumen y de brillo
;  en cada nota (ataque lento del operador que modula); aquí, cada nota de los
;  instrumentos 0 y 2 crece de volumen y entra un poco baja de tono.
; =============================================================================
            INCLUDE "mus_vars.inc"
            INCLUDE "mus_opt.inc"   ; opciones de la canción (build_rom.py): WAH
V_PTR       EQU 0
V_CNT       EQU 2
V_NOTE      EQU 3
V_INST      EQU 4
V_FRM       EQU 5
VA          EQU MUS_V
VB          EQU MUS_V+6
VC          EQU MUS_V+12
VD          EQU MUS_V+18
PSGA        EQU 0A0h
PSGW        EQU 0A1h

            ORG 4000h
            jp MUSFRAME

; ---- un cuadro de vídeo ---------------------------------------------------------
MUSFRAME:   call SFXSTEP            ; efecto de sonido (canal C), también con la música parada
            ld a,(MUS_ST)
            cp 1
            jr z,.play
            ret nc                  ; parada
            ld hl,INITV             ; arrancar: punteros, cnt = 1, voces calladas
            ld de,MUS_V
            ld bc,24
            ldir
            ld hl,0FFFFh
            ld (MUS_ACC),hl         ; la primera semicorchea suena ya
            ld a,1
            ld (MUS_ST),a
.play:      ld de,STEP60
            ld a,(MUS_HZ)
            rla
            jr nc,.hz
            ld de,STEP50
.hz:        ld hl,(MUS_ACC)
            add hl,de
            ld (MUS_ACC),hl
            jr nc,.out
            ld hl,VA
            call VTICK
            ld hl,VB
            call VTICK
            ld hl,VC
            call VTICK
            ld hl,VD
            call VTICK
.out:       ld a,0B8h               ; tonos A, B y C; ruido apagado; puerto B salida
            ld (MUS_MIX),a
            ld hl,VA
            ld c,0
            call VOUT
            ld hl,VB
            ld c,1
            call VOUT
            ld a,(MUS_SFX)
            or a
            jr nz,.sfx
            ld hl,VC
            ld c,2
            call VOUT
            call DRUMS
            ld a,7
            out (PSGA),a
            ld a,(MUS_MIX)
            out (PSGW),a
            ret
.sfx:       ld a,7                  ; canal C ocupado por un efecto (SFXSTEP): se
                                    ; respetan sus bits del mezclador (tono y ruido de C)
            out (PSGA),a
            in a,(0A2h)
            and 24h
            or 98h                  ; tonos A y B, sin ruido en A y B, puerto B salida
            out (PSGW),a
            ret

; ---- VTICK: HL = voz. Avanza una semicorchea --------------------------------------
VTICK:      inc hl
            inc hl
            dec (hl)                ; cnt
            ret nz
            push hl
            dec hl
            ld d,(hl)
            dec hl
            ld e,(hl)               ; DE = ptr
            ex de,hl                ; HL = ptr, DE = voz
.rd:        ld a,(hl)
            inc hl
            cp 0FFh
            jr nz,.ev
            ; fin: saltar al bucle (tabla LOOPS indexada por voz)
            ld a,e
            sub MUS_V&255           ; 0, 6, 12, 18
            rrca                    ; 0, 3, 6, 9: LOOPS tiene 3 bytes por voz
            ld c,a
            ld hl,LOOPS
            ld b,0
            add hl,bc               ; LOOPS + 0/3/6/9
            ld a,(hl)
            inc hl
            ld h,(hl)
            ld l,a
            jr .rd
.ev:        ld c,a                  ; C = nota / 60h silencio / batería
            ld a,(hl)
            inc hl
            ld b,a                  ; B = duración | inst << 6
            ex de,hl                ; HL = voz, DE = nuevo ptr
            ld (hl),e
            inc hl
            ld (hl),d
            inc hl
            ld a,b
            and 3Fh
            ld (hl),a               ; cnt
            inc hl
            ld (hl),c               ; nota
            inc hl
            ld a,b
            rlca
            rlca
            and 3
            ld (hl),a               ; inst
            inc hl
            ld (hl),0               ; cuadro
            pop hl
            ret

; ---- VOUT: HL = voz, C = canal 0..2. Escribe periodo y volumen --------------------
VOUT:       inc hl
            inc hl
            inc hl
            ld a,(hl)               ; nota
            cp 60h
            jr nc,.mute
            add a,a
            ld e,a
            ld d,0
            push hl
            ld hl,FREQTAB
            add hl,de
            ld e,(hl)
            inc hl
            ld d,(hl)
            pop hl
            IFDEF WAH
            push hl
            push bc
            inc hl
            ld a,(hl)               ; inst
            rra
            jr c,.nw                ; 1 y 3: sin wah
            inc hl
            ld a,(hl)               ; cuadro de la nota
            cp 4
            jr nc,.nw
            add a,4
            ld b,a                  ; periodo + periodo / 16, /32, /64, /128
            ld h,d
            ld l,e
.sh:        srl h
            rr l
            djnz .sh
            add hl,de
            ex de,hl
.nw:        pop bc
            pop hl
            ENDIF
            ld a,c
            add a,a
            out (PSGA),a
            ld a,e
            out (PSGW),a
            ld a,c
            add a,a
            inc a
            out (PSGA),a
            ld a,d
            out (PSGW),a
            inc hl
            ld a,(hl)               ; inst
            inc hl
            add a,a
            add a,a
            add a,a
            add a,a                 ; inst * 16
            ld e,(hl)               ; cuadro
            add a,e
            ld e,a
            ld d,0
            ld a,(hl)
            cp 15
            jr nc,.sus
            inc (hl)
.sus:       ld hl,ENVS
            add hl,de
            ld a,(hl)
            jr .vol
.mute:      xor a
.vol:       ld e,a
            ld a,c
            add a,8
            out (PSGA),a
            ld a,e
            out (PSGW),a
            ret

; ---- DRUMS: la batería se mezcla en el canal C --------------------------------------
;  nota de VD: 0 nada, 1 bombo, 2 caja, 3 charles, 40h|n timbal (nota n)
DRUMS:      ld hl,VD+V_NOTE
            ld a,(hl)
            or a
            ret z
            cp 60h
            ret z
            ld b,a
            inc hl
            inc hl
            ld a,(hl)               ; cuadro
            cp 6
            ret nc                  ; golpe terminado
            inc (hl)
            ld c,a                  ; C = cuadro
            ld a,b
            and 0C0h
            jr nz,.tom
            ld a,b
            dec a
            add a,a
            add a,a
            add a,a                 ; 8 bytes por golpe: 4 cuadros x (ruido|tono, volumen)
            add a,c
            add a,c
            ld e,a
            ld d,0
            ld a,c
            cp 4
            ret nc
            ld hl,DRUMTAB
            add hl,de
            ld a,(hl)               ; bit 7: tono (periodo alto = a * 16), si no ruido
            inc hl
            ld e,(hl)               ; volumen
            or a
            ret z
            jp m,.kick
            ; ruido en C, tono C apagado
            ld b,a
            ld a,6
            out (PSGA),a
            ld a,b
            out (PSGW),a
            ld a,(MUS_MIX)
            and 0DFh                ; ruido C encendido
            or 04h                  ; tono C apagado
            ld (MUS_MIX),a
            jr .cvol
.kick:      and 7Fh                 ; periodo = a * 16
            ld l,a
            ld h,0
            add hl,hl
            add hl,hl
            add hl,hl
            add hl,hl
            ld a,4
            out (PSGA),a
            ld a,l
            out (PSGW),a
            ld a,5
            out (PSGA),a
            ld a,h
            out (PSGW),a
.cvol:      ld a,10
            out (PSGA),a
            ld a,e
            out (PSGW),a
            ret
.tom:       ld a,c
            cp 5
            ret nc
            ld a,b
            and 3Fh
            add a,a
            ld e,a
            ld d,0
            ld hl,FREQTAB
            add hl,de
            ld e,(hl)
            inc hl
            ld d,(hl)               ; periodo de la nota, baja con los cuadros
            ld b,c
            inc b
.tl:        ex de,hl                ; + 1/8 por cuadro
            ld e,l
            ld d,h
            srl d
            rr e
            srl d
            rr e
            srl d
            rr e
            add hl,de
            ex de,hl
            djnz .tl
            ld a,4
            out (PSGA),a
            ld a,e
            out (PSGW),a
            ld a,5
            out (PSGA),a
            ld a,d
            out (PSGW),a
            ld a,c
            ld hl,TOMVOL
            ld e,a
            ld d,0
            add hl,de
            ld e,(hl)
            jr .cvol

TOMVOL:     db 14,13,11,9,6
;            ruido/tono, vol x 4 cuadros
DRUMTAB:    db 80h+20,14, 80h+40,12, 80h+70,9, 0,0          ; bombo: tono que cae
            db 5,14, 7,12, 9,10, 11,7                       ; caja
            db 1,9, 0,0, 0,0, 0,0                           ; charles
            db 1,12, 1,10, 2,8, 3,6                         ; platillo

; envolventes de volumen por cuadro (16 entradas, la última se mantiene)
            IFDEF WAH
ENVS:       db 7,9,11,13,14,14,13,12,11,10,10,9,9,9,9,9           ; 0 melodía con wah
            db 14,13,12,11,10,10,9,9,8,8,8,8,8,8,8,8              ; 1 bajo
            db 6,8,10,11,12,12,11,10,9,9,8,8,8,8,8,8              ; 2 segunda voz con wah
            db 12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12    ; 3 sirena: fija
            ELSE
ENVS:       db 13,14,13,13,12,12,12,11,11,11,11,10,10,10,10,10   ; 0 melodía
            db 14,13,12,11,10,10,9,9,8,8,8,8,8,8,8,8              ; 1 bajo
            db 11,11,10,10,9,9,9,8,8,8,7,7,7,7,7,7                ; 2 acompañamiento
            db 11,11,10,10,9,9,8,8,8,7,7,7,7,7,7,7                ; 3 eco de la melodía
            ENDIF

            INCLUDE "mus_tab.inc"

INITV:      dw MUS_A
            db 1,60h,0,0
            dw MUS_B
            db 1,60h,0,0
            dw MUS_C
            db 1,60h,0,0
            dw MUS_D
            db 1,60h,0,0
LOOPS:      dw MUS_A_LOOP
            db 0
            dw MUS_B_LOOP
            db 0
            dw MUS_C_LOOP
            db 0
            dw MUS_D_LOOP

            INCLUDE "mus_cur.inc"
; =============================================================================
;  SFXSTEP: efectos de sonido de la recreativa en el canal C, un paso por cuadro de
;  vídeo. PSGFXR (rom_musica.asm) deja en SFX_REQ el efecto pedido + 1. Cada efecto
;  (sfx_data.inc, generado por sfx/efectos.py) es una lista de pasos:
;    byte 0: volumen (bits 0-3) | 10h ruido | 20h tono | (cuadros - 1) << 6
;    luego el periodo del ruido si lo hay y el del tono (2 bytes) si lo hay; FFh = fin
; =============================================================================
SFXSTEP:    ld a,(SFX_REQ)
            or a
            jr z,.run
            dec a
            ld c,a
            xor a
            ld (SFX_REQ),a
            ld a,c
            cp SFX_N
            jr nc,.run
            add a,a
            ld l,a
            ld h,0
            ld de,SFXTAB
            add hl,de
            ld a,(hl)
            inc hl
            ld h,(hl)
            ld l,a
            or h
            jr z,.run
            ld (SFX_PTR),hl
            xor a
            ld (SFX_HOLD),a
            inc a
            ld (MUS_SFX),a
.run:       ld a,(MUS_SFX)
            or a
            ret z
            ld a,(SFX_HOLD)
            or a
            jr z,.next
            dec a
            ld (SFX_HOLD),a
            ret
.next:      ld hl,(SFX_PTR)
            ld a,(hl)
            inc hl
            cp 0FFh
            jr z,.end
            ld b,a
            rlca
            rlca
            and 3
            ld (SFX_HOLD),a
            ld c,24h                ; mezclador de C: 1 = apagado (tono bit 2, ruido bit 5)
            bit 4,b
            jr z,.nn
            res 5,c
            ld a,6
            out (PSGA),a
            ld a,(hl)
            inc hl
            out (PSGW),a
.nn:        bit 5,b
            jr z,.nt
            res 2,c
            ld a,4
            out (PSGA),a
            ld a,(hl)
            inc hl
            out (PSGW),a
            ld a,5
            out (PSGA),a
            ld a,(hl)
            inc hl
            out (PSGW),a
.nt:        ld (SFX_PTR),hl
            ld a,10
            out (PSGA),a
            ld a,b
            and 0Fh
            out (PSGW),a
            ld a,7
            out (PSGA),a
            in a,(0A2h)
            and 0DBh
            or c
            out (PSGW),a
            ret
.end:       xor a
            ld (MUS_SFX),a
            ld a,10
            out (PSGA),a
            xor a
            out (PSGW),a
            ret
            INCLUDE "sfx_data.inc"

MUS_END:
            ASSERT MUS_END <= 6000h
