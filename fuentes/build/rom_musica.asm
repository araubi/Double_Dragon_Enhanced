; =============================================================================
;  MegaROM: música durante las misiones (solo ROM).
;  El código va en F400h-FBFFh, memoria que el juego no toca; el arranque lo copia
;  (item HIGH). Las canciones están en bancos propios (musbanks.inc, generado).
;
;  El juego corre siempre sin interrupciones y a unos 9 cuadros por segundo, así
;  que el compás se mide con el indicador de cuadro del VDP (bit 7 del estado),
;  sondeado en puntos del juego separados menos de un cuadro de vídeo (MUSPOLL):
;  bucles de volcado, bucle de dibujo de figuras, entrada del teclado/joystick,
;  scroll y esperas. Las esperas de bucle vacío se cambian por esperas de cuadros.
;  El canal C es de los efectos de sonido mientras suenan (MUS_SFX).
;
;  Canciones: misión 1 y 4 "Slums", 2 y 5A "Industrial Area", 3A y 3B "Woods",
;  5B "Enemy Headquarters", fin de misión "Mission Complete", final "Reunion
;  with Marian"; con los jefes (último Abobo de la 1, Jeff de la 2, Abobos del final
;  de la 3B, el del final de la 4) "The Entrance of Abobo the Giant", y en la escalera
;  de la 5B la del menú (FRAME5B). Música de Double Dragon (Technos Japan, 1987), Kazunaka Yamane.
; =============================================================================
                                        ; MB_xx: musbanks.inc (incluido en rom_resident.asm)

; ---- enganches en el código común ---------------------------------------------
            ORG 0E613h              ; principio del volcado de cada cuadro (NOPs libres)
            call FRAME5B            ; (rom_resident.asm; sigue en FRAMEHK)
            ORG 0E66Fh              ; PFDIFF: cambio de bloque de 256 celdas
            call PPF
            ORG 0E292h              ; PFUP: cambio de fila
            call PPU
            ORG 0E425h              ; HUDHALF: siguiente carácter
            call PHUD
            nop
            ORG 0E8BAh              ; scroll hacia un lado: fin de cada vuelta
            jp SCRP1
            ORG 0E926h              ; scroll hacia el otro
            jp SCRP2
            ORG 06E9h               ; volcado completo de patrones
            call P6E9
            push bc
            ORG 0A3Fh
            jp P6ROW
            nop
            ORG 0E14Ch              ; lectura de controles (también en las pantallas
            jp PE14C                ; de título y de fin de misión)
            ORG 0E30Ah              ; efectos de sonido: en el canal C
            jp PSGFXR
            ORG 0DD4h               ; joystick: sin pisar el mezclador de la música
            jp JOYFIXR
            ORG SETMIS              ; principio de cada misión: su canción
            jp MUSMIS

            ORG 0F400h
HIGH_START:
; ---- MUSPOLL: si ha empezado un cuadro de vídeo, un paso de música ---------------
;      Conserva todos los registros y los indicadores. No debe llamarse entre las
;      dos escrituras de una dirección del VDP ni con la pila apuntando a datos.
MUSPOLL:    push af
            in a,(VDPC)
            rlca
            jr c,.tick
            pop af
            ret
.tick:      call MUSANY
            jr z,.off
            pop af
            jp MUSFRM
.off:       pop af
            ret
; ---- MUSANY: NZ si hay algo que tocar (canción o efecto de sonido). Solo cambia A y F
MUSANY:     ld a,(MUS_ST)
            cp 2
            ret nz
            ld a,(MUS_SFX)
            or a
            ret nz
            ld a,(SFX_REQ)
            or a
            ret

; ---- MUSFRM: un cuadro de música. Pone el cartucho en la página 1 mientras suena,
;      así que usa su propia pila en la página 0 (la del juego está en 5Bxxh).
;      Si el cartucho y la RAM de la página 1 están en slots primarios distintos
;      basta con cambiar el puerto A8h (el subslot del cartucho ya lo dejó puesto
;      el cargador); si no, SETSLOT completo.
MUSFRM:     push af
            push bc
            push de
            push hl
            ld (MUS_SP),sp
            ld sp,MSTACK
            ld a,(SLOT_RAM1)
            ld b,a
            ld a,(SLOT_CART)
            xor b
            and 3
            jr z,.slow
            in a,(0A8h)
            ld c,a
            and 0F3h
            ld b,a
            ld a,(SLOT_CART)
            and 3
            add a,a
            add a,a
            or b
            out (0A8h),a
            push bc
            ld a,(MUS_BK)
            ld (6000h),a            ; ASCII8: 4000-5FFF = reproductor y canción
            call 4000h
            pop bc
            ld a,c
            out (0A8h),a
            jr .end
.slow:      ld a,(SLOT_CART)
            ld b,1
            call SETSLOT
            ld a,(MUS_BK)
            ld (6000h),a
            call 4000h
            ld a,(SLOT_RAM1)
            ld b,1
            call SETSLOT
.end:       ld sp,(MUS_SP)
            pop hl
            pop de
            pop bc
            pop af
            ret

; ---- puntos de sondeo en el código común -------------------------------------------
PPF:        inc d
            inc h
            call MUSPOLL
            ld a,h
            ret
PPU:        inc hl
            inc d
            call MUSPOLL
            ld a,d
            ret
PHUD:       inc l
            ld a,l
            and 0Fh
            call z,MUSPOLL          ; cada 16 caracteres
            ld a,l
            and 3Fh
            ret
P6E9:       di
            jp MUSPOLL              ; lee el estado del VDP como hacía el original
P6ROW:      call MUSPOLL
            dec a
            jp nz,0702h
            jp 0A43h
PE14C:      call MUSPOLL
            ld c,0
            and a
            jp 0E14Fh
; scroll: la pila apunta a los datos durante la copia; cada 8 vueltas se recupera
; la pila de verdad (guardada en E865h) para sondear. La vuelta siguiente vuelve a
; cargar SP desde IX, y IX/IY no los toca la música.
SCRP1:      ld hl,0E937h
            ld a,(hl)
            and 7
            jr nz,.n
            ld sp,(0E865h)
            call MUSPOLL
.n:         dec (hl)
            jp nz,0E87Ch
            jp 0E8C0h
SCRP2:      ld hl,0E937h
            ld a,(hl)
            and 7
            jr nz,.n
            ld sp,(0E865h)
            call MUSPOLL
.n:         dec (hl)
            jp nz,0E8E8h
            jp 0E92Dh

; ---- elegir canción --------------------------------------------------------------
SETSONG:    ld (MUS_BK),a           ; A = banco: suena desde el principio
            xor a
            ld (MUS_ST),a
            ld (MUS_SFX),a
            ret
SONGTAB:    db MB_02, MB_06, MB_07, MB_07, MB_02, MB_06, MB_08     ; misiones 1-7
MUSRESUME:  push af                 ; tras GAME OVER con créditos la misión sigue sin
            ld a,(MUS_ABO)          ; pasar por SETMIS: si ya había salido el jefe, su
            rla                     ; canción (MUS_BK) otra vez desde el principio
            jr nc,.m
            ld a,(MUS_BK)
            call SETSONG
            pop af
            ret
.m:         pop af
            ld a,(5B13h)            ; si no, la canción de la misión
MUSSONG:    push af                 ; A = misión 1..7: su canción desde el principio
            xor a                   ; música de jefe otra vez posible (FRAMEHK)
            ld (MUS_ABO),a
            ld (JPREV),a
            ld (JPREV+1),a
            ld (JPREV+2),a
            pop af
            push af
            push hl
            push de
            dec a
            cp 7
            jr nc,.x
            ld e,a
            ld d,0
            ld hl,SONGTAB
            add hl,de
            ld a,(hl)
            call SETSONG
.x:         pop de
            pop hl
            pop af
            ret
MUSMIS:     ld (MUS_PEND),a         ; SETMIS, al cargar cada misión: silencio en la
            push af                 ; pantalla de pulsar el botón; su canción empieza
            push hl                 ; con el primer cuadro de juego (FRAMEHK)
            call MUSMUTE
            pop hl
            pop af
            push hl                 ; las tres instrucciones que ocupa el salto
            push de
            dec a
            jp SETMIS+3
MENUSTART:  ld a,(MUS_BK)           ; menú: la música de presentación, desde el
            cp MB_01                ; principio si sonaba otra o estaba parada
            jr nz,.r
            ld a,(MUS_ST)
            cp 2
            jr nz,.k
.r:         call MUSMUTE
            ld a,MB_01
            call SETSONG
.k:         jp 0D03h
MUSMUTE:    ld a,2                  ; parar y callar los tres canales
            ld (MUS_ST),a
            ld hl,PSGMUTE
            jp PSGFX.go
PSGMUTE:    db 8,0, 9,0, 10,0, 0FFh

; ---- FRAMEHK: al principio de cada cuadro. Música de jefe: cuando aparece en un hueco
;      de enemigo una figura del tipo y con la energía inicial de un jefe de la tabla
;      JEFES, suena su canción. La energía inicial es la de su registro en la tabla de
;      enemigos y distingue al jefe de otros del mismo tipo (el primer Abobo de la
;      misión 1 sale con 50h y el último con 5Ah). El registro se carga en el hueco antes
;      de que salga la figura: mientras espera (estado 0) con el tipo y la energía del jefe,
;      el hueco queda «armado» (JPREV = FFh), y cuando se pone en uso suena la canción,
;      tenga la energía que tenga (Rubén, 2026-10-25: Jeff salía con el último bloque y
;      si le pegaban antes del primer cuadro ya no tenía su energía y no sonaba).
;      MUS_ABO bit 7 = ya ha cambiado. MUSSONG borra los dos. Conserva los registros.
JEFES:      ;  misión, tipo, energía inicial, canción
            ; (energías como en la recreativa, ENERGIA en build_ram.py)
            db 1, 3, 112, MB_03     ; 1: último Abobo (registro 9680h; el primero, 103)
            db 2, 0, 131, MB_03     ; 2: Jeff
            db 4, 3, 140, MB_03     ; 3B: los dos Abobos del final (el del principio, 112)
            db 5, 3, 150, MB_03     ; 4: el Abobo del final (registro 978Bh)
            db 0
JPREV:      db 0, 0, 0
FRAMEHK:    push af
            ld a,(MUS_PEND)         ; misión recién cargada: su canción ya
            or a
            jr z,.p
            call MUSSONG            ; (conserva los registros)
            xor a
            ld (MUS_PEND),a
.p:         push hl
            push de
            push bc
            ld a,(5B13h)
            ld c,a
            ld hl,JEFES
.t:         ld a,(hl)
            or a
            jr z,.x                 ; esta misión no tiene
            cp c
            jr z,.m
            inc hl
            inc hl
            inc hl
            inc hl
            jr .t
.m:         push ix
            inc hl
            ld e,(hl)               ; E = tipo
            inc hl
            ld d,(hl)               ; D = energía inicial
            inc hl
            push hl                 ; -> canción
            ld ix,(MIS_P1)
            ld bc,36
            add ix,bc               ; primer hueco de enemigo
            ld hl,JPREV
            ld bc,03FFh             ; C <> FFh si ha aparecido el jefe
.s:         ld a,(ix+15)
            and 0Fh
            cp e
            jr nz,.z                ; no es del tipo
            ld a,(ix+0)
            or a
            jr nz,.u                ; en uso
            ld a,(ix+17)            ; esperando: armado (FFh) si tiene la energía del jefe
            xor d
            sub 1
            sbc a,a
            jr .n
.u:         ld a,(hl)
            inc a
            jr nz,.z                ; no estaba armado
            inc c                   ; ha salido el jefe
.z:         xor a
.n:         ld (hl),a
            inc hl
            push de
            ld de,18
            add ix,de
            pop de
            djnz .s
            pop hl
            pop ix
            ld a,(MUS_ABO)
            or a
            jr nz,.x                ; ya ha cambiado
            inc c
            jr z,.x                 ; no ha aparecido
            ld a,(hl)
            call SETSONG
            ld a,80h
            ld (MUS_ABO),a
.x:         pop bc
            pop de
            pop hl
            pop af
            jp MUSPOLL

; ---- fin de misión, game over y final ------------------------------------------------
MCOMPL:     xor a                   ; lo que hacía el original: (5B1Bh) = 0
            ld (5B1Bh),a
            ld a,MB_04              ; "Mission Complete"
            jp SETSONG
GOVER:      call MUSMUTE            ; GAME OVER: silencio
            ld hl,484Bh             ; la instrucción que ocupa la llamada
            ret
ENDSONG:    ld a,MB_09              ; Willy derrotado: música del final
            call SETSONG
            ld hl,4842h
            ret
; ENDWAIT: en lugar de la pausa de ~3,8 s tras "MAY YOU LIVE HAPPILY FOREVER",
; se espera a que acabe una vuelta de la música del final o a que se pulse el
; disparo (pasados los 3,8 s). Luego el logo de la recreativa (ENDLOGO).
ENDWAIT:    ld hl,0
            ld (MUS_CNT),hl
.w:         call WAITF
            ld hl,(MUS_CNT)
            inc hl
            ld (MUS_CNT),hl
            ld de,-1950             ; ~32,5 s a 60 Hz (39 s a 50 Hz)
            add hl,de
            jr c,.fin
            ld hl,(MUS_CNT)
            ld de,-228              ; 3,8 s
            add hl,de
            jr nc,.w
            ld a,(5B19h)
            call 0E14Ch
            bit 4,a
            jr z,.w
.fin:       jp ENDLOGO              ; el logo y la partida otra vez (rom_resident.asm)
LOGOITEM:   db SCR_BANK             ; ENDLOGO: el logo de la pantalla de carga a 9056h
            dw SCR_OFS, 9056h, 3000h

; ---- esperas: cuadros de vídeo en vez de bucles vacíos ------------------------------
; DELAY sustituye a "LD BC,FFFFh / DEC BC / ... / DEC E / JR NZ": E unidades de
; 65535 vueltas de 26 ciclos (0,476 s) = 28 cuadros a 60 Hz o 24 a 50 Hz.
DELAY:
.u:         ld b,28
            ld a,(MUS_HZ)
            rla
            jr nc,.w
            ld b,24
.w:         call WAITF
            djnz .w
            dec e
            jr nz,.u
            xor a
            ld b,a
            ld c,a
            ret
WAITF:      in a,(VDPC)             ; espera el siguiente cuadro y da un paso
            rlca
            jr nc,WAITF
            call MUSANY
            ret z
            jp MUSFRM

; ---- efectos de sonido en el canal C -------------------------------------------------
PSGFXR:     inc a                   ; A = efecto (dd_sonido.asm): lo empieza el
            ld (SFX_REQ),a          ; reproductor de los bancos (mus_player.asm) en el
            ret                     ; siguiente cuadro de vídeo
CASSFX      EQU PSGFXR              ; (dd_patches.asm: la cinta usa su propia rutina)

; ---- joystick: R7 se lee y se cambian solo los bits de los puertos -------------------
JOYFIXR:    ld a,7
            out (PSGA),a
            in a,(PSGR)
            and 3Fh
            or 80h                  ; puerto B salida, puerto A entrada
            out (PSGW),a
            ld a,15
            out (PSGA),a
            in a,(PSGR)
            and 80h
            or 3Fh
            out (PSGW),a
            ld a,14
            out (PSGA),a
            jp 0DE6h

; ---- puntos de sondeo de cada misión (generado por build_rom.py) --------------------
            INCLUDE "mus_polls.inc"
; ---- tablas de carga de las misiones (generado; ROMLOAD) -----------------------------
            INCLUDE "romitems2.inc"
            INCLUDE "dd_figuras.asm"
HIGH_END:
            ASSERT HIGH_END <= 0FC00h
