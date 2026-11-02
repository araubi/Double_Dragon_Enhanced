; =============================================================================
;  Sprites de color para los jugadores (solo ROM).
;  Las figuras se pintan en el buffer 2C00h línea a línea con pares máscara/tinta
;  (DRAWM/DRAWI de dd_figuras.asm). De cada jugador se guarda su relleno (su
;  tinta: lo blanco pasa a color y el papel sigue negro; Rubén, 2026-10-24), y las figuras que se pintan
;  después, que están delante, le borran su silueta (AND máscara). Al empezar el
;  volcado del cuadro el relleno sale en sprites de 16x16: azul oscuro el jugador 1
;  y rojo el jugador 2 (3 bandas de 16 líneas x hasta 3 sprites cada uno).
;  El jugador 2 ya no va en negativo; Jeff sí (como iba antes el jugador 2) y ya
;  no se colorea de rojo por celdas (JMARK desactivado).
;  Para no gastar tiempo, FIGSEL elige la rutina de cada figura: la de siempre si
;  no toca a ningún jugador, DRAWMC (dibujo y relleno en el mismo bucle) para un
;  jugador y DRAWMO/DRAWIO (borra su silueta del relleno y luego la de siempre)
;  para las que tapan a un jugador.
;  Relleno: columna k (0..5) en la página BUFPG+k, línea i en el byte bajo
;  base+i (jugador 1: 40h, jugador 2: 70h); variables en los bytes A0h-BFh de
;  las páginas 1Eh y 1Fh. Todo en huecos libres de la página de sombra del
;  marcador (bytes bajos 40h-BFh; ver dd_jeff.asm).
;  Código en huecos sin uso: página 0 tras BOOTITEMS, E828h, E97Ah, el relleno
;  antes de FLIPTAB (dd_figuras.asm) y los items SPRA-SPRD (build_rom.py).
; =============================================================================
BUFPG       EQU 1Eh
NCOL        EQU 6
NLIN        EQU 48
; por jugador, 16 bytes en PT
PT          EQU 1EA0h
P_L0        EQU 0                   ; primera línea
P_C0        EQU 1                   ; columna (con signo)
P_R0        EQU 2                   ; fila (unidades de 4 líneas)
P_PW        EQU 3                   ; ancho máximo en bytes
P_K         EQU 4                   ; base - primera línea
P_BASE      EQU 5                   ; byte bajo de su primera línea en el relleno
P_LIM       EQU 6                   ; figura que lo tapa: bytes hasta salir de su relleno
P_J0        EQU 7                   ;   primer byte dentro de su relleno
P_PG0       EQU 8                   ;   página de ese byte
P_DOFF      EQU 9                   ;   desplazamiento de ese byte en los pares
; resto de variables (sin valor inicial: SPROFF y SPRUPD las ponen)
ACT         EQU 1FA0h               ; bit 0/1: jugador 1/2 pintado en este cuadro
CUR         EQU ACT+1               ; figura que se pinta: 0 otra, 1/2 jugador
OCC         EQU ACT+2               ; jugadores ya pintados que tapa esta figura
CPWP        EQU ACT+3               ; (2) ancho máximo del jugador que se pinta
SPN         EQU ACT+9               ; sprites que se ven
SQ          EQU ACT+10              ; jugador de los sprites que se escriben
SPW         EQU ACT+11              ; su ancho
PADR        EQU ACT+12              ; (2) siguiente hueco de patrones
ATTR        EQU ACT+14              ; (4)
; doble juego de sprites: patrones en 3800h o 3C00h y atributos en 1B00h o 1B80h
; (R5 = 36h o 37h). Se escribe el que no se ve y R5 cambia cuando el volcado de
; patrones (PFUP) pasa por la mitad de los jugadores, para que sprite y dibujo
; cambien a la vez (antes el sprite iba un volcado por delante).
R5P         EQU ACT+18              ; R5 pendiente (0 = nada)
DISP        EQU ACT+19              ; R5 que se ve
SATROW      EQU ACT+20              ; fila de PFUP (+1) en que se cambia
OLDP        EQU ACT+21              ; (2) líneas máx./mín. de los jugadores del cuadro anterior
HTOG        EQU ACT+23              ; mitad del marcador que se compara
            ASSERT HTOG+1 <= 1FC0h

; ---- enganches ---------------------------------------------------------------
            ORG 0E613h              ; principio del volcado de cada cuadro
            call SPRFRM
            ORG 0AADh               ; redibujado de pantalla completa: sin sprites
            jp SPRAAD
            ORG FADEHOOK            ; fundido de fin de misión: sin sprites
            jp SPRFADE
            ORG JMARK               ; Jeff ya no se colorea por celdas
            ret
            ORG 0E292h              ; PFUP: cambio de fila (antes call PPU)
            call PPUS
            ORG 0E299h              ; PFUP: final (antes ld hl,FID)
            jp PFDN
            ORG 0E3DFh              ; HUDDIFF: una mitad del marcador por cuadro
            jp HUDALT

; ---- rutinas cortas (página 0, tras BOOTITEMS) ---------------------------------
            ORG BOOTITEMS+7*NBOOTITEMS
; A = jugador (1/2) -> HL = su entrada de PT. Solo cambia A, F, H y L
PTE:        dec a
            rlca
            rlca
            rlca
            rlca
            add a,PT&255
            ld l,a
            ld h,PT>>8
            ret
; HL = dirección de VRAM para escribir
VWR:        ld a,l
            out (99h),a
            ld a,h
            or 40h
            out (99h),a
            ret
; DE = destino en 2C00h -> A = línea. Cambia C
LINEOF:     ld a,e
            rlca
            rlca
            rlca
            and 7
            ld c,a
            ld a,d
            sub 2Ch
            add a,a
            add a,a
            add a,a
            or c
            ret
            ASSERT $ <= 00B0h

; ---- selección de figura -------------------------------------------------------
            ORG 0E97Ah              ; hueco libre (ceros, sin uso) tras E964h
; En lugar de BIT 3,(HL) / LD HL,DRAWM / JR Z / LD HL,DRAWI del dibujo de figuras.
; HL = descriptor, B = fila en unidades de 4 líneas, C = columna. Sale HL = rutina.
FIGSEL:     push de
            push bc
            ex de,hl
            ld hl,(MIS_P1)
            ld bc,5
            add hl,bc
            ld b,5                  ; jugador 1, jugador 2 y tres enemigos
.l:         ld a,(hl)
            inc hl
            cp e
            jr nz,.n
            ld a,(hl)
            cp d
            jr z,.f
.n:         ld a,17
            add a,l
            ld l,a
            adc a,h
            sub l
            ld h,a
            djnz .l
.def:       xor a
            ld (CUR),a
            ex de,hl
            bit 3,(hl)              ; como venga: bit 3 = en negativo
            ld hl,DRAWM
            jr z,.occ
.neg:       ld hl,DRAWI
.occ:       pop bc
            push hl
            ld a,(CUR)
            cpl
            ld hl,ACT
            and (hl)
            ld e,a                  ; jugadores ya pintados (no esta figura)
            ld d,0
            ld a,1
            call BOXQ
            ld a,2
            call BOXQ
            pop hl
            ld a,d
            ld (OCC),a
            ld a,(CUR)
            or a
            jr z,.o
            ld hl,DRAWMC            ; jugador: dibujo y relleno a la vez
            jr .x
.o:         or d
            jr z,.x                 ; ni jugador ni encima de uno: tal cual
            ld a,l
            cp DRAWM&255
            ld hl,DRAWMO
            jr z,.x
            ld hl,DRAWIO
.x:         pop de
            ret
.f:         ld a,b
            cp 4
            jr c,.en
            ld a,6
            sub b                   ; 1 = jugador 1, 2 = jugador 2
            ld (CUR),a
            pop bc
            push bc
            call PSETUP
            ld hl,DRAWM
            jr .occ
.en:        ld bc,15-6
            add hl,bc
            ld a,(hl)
            or a
            jr nz,.def              ; no es Jeff
            ld (CUR),a
            ld hl,DRAWI             ; Jeff: en negativo
            jr .occ
; A = jugador: si está en E y su recuadro toca el de la figura (B fila, C columna),
; D |= A y apunta qué bytes de cada línea de la figura caen en su relleno
BOXQ:       push af
            and e
            jr z,.no
            pop af
            push af
            push bc
            call PTE
            inc hl
            ld a,c
            sub (hl)
            ld c,a                  ; C = columna de la figura respecto a la suya
            add a,5
            cp 11                   ; columnas: 6 de ancho como mucho
            jr nc,.no2
            inc hl
            ld a,b
            sub (hl)
            add a,15
            cp 27                   ; filas: 12 el jugador, hasta 16 la figura
            jr nc,.no2
            ld a,l
            add a,P_LIM-P_R0
            ld l,a
            ld a,NCOL
            sub c
            ld (hl),a               ; LIM
            inc hl
            xor a
            sub c
            jp p,.j
            xor a
.j:         ld (hl),a               ; J0
            ld b,a
            inc hl
            add a,c
            add a,BUFPG
            ld (hl),a               ; PG0
            inc hl
            ld a,b
            add a,a
            ld (hl),a               ; DOFF
            pop bc
            pop af
            or d
            ld d,a
            ret
.no2:       pop bc
.no:        pop af
            ret
            ASSERT $ <= 0EA60h

            ORG 0E828h              ; hueco libre tras los trampolines del scroll
; IX = entrada de PT de un jugador ya pintado, C = línea; B = ancho, DE = destino,
; HL = pares de una línea de una figura que está delante: le borra su silueta del
; relleno. Lo conserva todo menos A y F.
OFX:        push de
            push bc
            push hl
            ld a,c
            add a,(ix+P_K)          ; byte bajo de la línea en su relleno
            ld e,a
            sub (ix+P_BASE)
            cp NLIN
            jr nc,.x
            ld a,b
            cp (ix+P_LIM)
            jr c,.m
            ld a,(ix+P_LIM)         ; hasta LIM
.m:         sub (ix+P_J0)           ; desde J0
            jr z,.x
            jr c,.x
            ld b,a
            ld d,(ix+P_PG0)
            ld a,(ix+P_DOFF)
            add a,l
            ld l,a
            adc a,h
            sub l
            ld h,a
.o:         ld a,(de)
            and (hl)
            ld (de),a
            inc d
            inc hl
            inc hl
            djnz .o
.x:         pop hl
            pop bc
            pop de
            ret
            ASSERT $ <= 0E865h

; ---- dibujo con relleno ----------------------------------------------------------
            ORG 2440h               ; hueco de la página de sombra (item SPRA)
; Jugador: como DRAWM (B = ancho, C = columna, HL = pares, DE = destino) y además
; guarda el relleno de la línea; antes, lo que tapa de otro jugador
DRAWMC:     ld a,(OCC)
            or a
            call nz,OCCL
            ld a,b
            cp NCOL+1
            jr c,.w
            ld a,NCOL
.w:         push hl
            ld hl,(CPWP)
            cp (hl)
            jr c,.k
            ld (hl),a
.k:         inc hl
            push af
            push bc
            call LINEOF
            pop bc
            add a,(hl)
            exx
            ld l,a
            ld h,BUFPG
            exx
            pop af
            pop hl
            cp b
            jr nz,.sep              ; más de 6 bytes
            ld a,c
            cp 20h
            jr nc,.sep
            add a,b
            cp 21h
            jr nc,.sep              ; se sale por un lado
.l:         ld c,(hl)
            inc hl
            ld a,(hl)               ; relleno = la tinta
            exx
            ld (hl),a
            inc h
            exx
            ld a,(de)
            and c
            or (hl)
            ld (de),a
            inc hl
            inc de
            djnz .l
            ret
.sep:       push hl                 ; el relleno aparte y luego DRAWM
            push bc
            ld a,b
            cp NCOL+1
            jr c,.v
            ld a,NCOL
.v:         ld b,a
.c:         inc hl
            ld a,(hl)               ; la tinta
            inc hl
            exx
            ld (hl),a
            inc h
            exx
            djnz .c
            pop bc
            pop hl
            jp DRAWM
            ASSERT $ <= 24C0h

            ORG 0F398h              ; trabajo de la BIOS, sin uso en la ROM (item SPRD)
; las que tapan a un jugador: su silueta fuera del relleno y luego la de siempre
DRAWMO:     call OCCL
            jp DRAWM
DRAWIO:     call OCCL
            jp DRAWI
; A = jugador, B = fila (x4 líneas), C = columna: lo apunta y borra su relleno
PSETUP:     push af
            ld hl,ACT
            or (hl)
            ld (hl),a
            pop af
            ld e,40h
            cp 1
            jr z,.b
            ld e,70h
.b:         call PTE
            ld a,b
            add a,a
            add a,a
            ld (hl),a               ; primera línea
            ld d,a
            inc hl
            ld (hl),c               ; columna
            inc hl
            ld (hl),b               ; fila
            inc hl
            ld (CPWP),hl
            ld c,(hl)               ; ancho del cuadro anterior (ya sin uso: PCLR borra las 6)
            ld (hl),0               ; ancho
            inc hl
            ld a,e
            sub d
            ld (hl),a               ; base - primera línea
            inc hl
            ld (hl),e               ; base
            jp PCLR                 ; y borra su relleno
; marcador: una mitad (filas 0-1 o 22-23) en cada cuadro en vez de las dos; cada
; comparación de una mitad cuesta unos 15.000 T y casi nunca hay cambios
HUDALT:     ld hl,HTOG
            inc (hl)
            bit 0,(hl)
            ld bc,4058h
            ld l,0
            jp z,HUDHALF
            ld bc,505Ah
            ld l,0C0h
            jp HUDHALF
; cambio de fila de PFUP (D = fila siguiente): el de siempre y, en su fila, el cambio
PPUS:       call PPU
            ld a,(SATROW)
            cp d
            call z,SATSW
            ld a,d
            ret
            ASSERT $ <= 0F400h

; ---- sprites de cada cuadro ----------------------------------------------------
            ORG 2540h               ; hueco de la página de sombra (item SPRB)
SPRUPD:     push af
            push bc
            push de
            push hl
            ld a,0C2h               ; sprites de 16x16
            out (99h),a
            ld a,81h
            out (99h),a
            call SPBANK             ; A = 1
            call SPQ
            ld a,2
            call SPQ
            ld a,(SPN)
            add a,a
            add a,a
            ld l,a
            ld h,1Bh
            call VWR
            ld a,0D0h               ; fin de la lista
            out (98h),a
            call SPEND
            xor a
            ld (ACT),a
            pop hl
            pop de
            pop bc
            pop af
            ret
; A = jugador: sus sprites, banda a banda, solo en las columnas que usa
SPQ:        ld (SQ),a
            ld hl,ACT
            and (hl)
            ret z                   ; no se ha pintado
            ld a,(SQ)
            call PTE
            ld e,(hl)               ; E = primera línea
            inc hl
            ld d,(hl)               ; D = columna
            inc hl
            inc hl
            ld a,(hl)
            ld (SPW),a              ; ancho
            inc hl
            inc hl
            ld l,(hl)               ; base del relleno
            ld h,BUFPG              ; HL = relleno, columna 0
            ld b,3
.band:      push bc
            push de
            push hl
            ld a,(SPW)
.spr:       or a
            jr z,.nb
            push af
            push de
            push hl
            call SPONE
            pop hl
            pop de
            pop af
            inc h
            inc h
            inc d
            inc d
            sub 2
            jr z,.nb
            jr nc,.spr
.nb:        pop hl
            pop de
            pop bc
            ld a,16
            add a,l
            ld l,a
            ld a,16
            add a,e
            ld e,a
            djnz .band
            ret
            ASSERT $ <= 25C0h

            ORG 2600h               ; hueco de la página de sombra (item SPRC)
; HL = relleno (columna izquierda, primera línea de la banda), E = línea, D = columna.
; El dibujo va al siguiente hueco de patrones (PADR); si sale vacío o fuera de la
; pantalla, ese hueco se aprovecha para el siguiente.
SPONE:      push hl
            ld hl,(PADR)
            call VWR
            pop hl
            ld c,0
            call SPCOL
            inc h
            call SPCOL
            ld a,c
            or a
            ret z                   ; vacío
            ld a,d
            ld b,0
            cp 20h
            jr c,.x
            add a,4
            cp 4
            ret nc                  ; fuera por un lado
            ld b,80h                ; reloj adelantado: X-32
.x:         rlca
            rlca
            rlca
            ld (ATTR+1),a
            ld a,e
            add a,15                ; zona de juego desde la línea 16; Y = línea-1
            ld (ATTR),a
            ld a,(SQ)
            add a,6                 ; jugador 1: 7 (azul celeste), 2: 8 (rojo)
            or b
            ld (ATTR+3),a
            ld a,(SPN)
            add a,a
            add a,a
            ld (ATTR+2),a
            ld l,a
            ld h,1Bh
            call VWR
            ld hl,ATTR
            ld b,4
.a:         ld a,(hl)
            out (98h),a
            inc hl
            djnz .a
            ld hl,SPN
            inc (hl)
            ld hl,(PADR)
            ld bc,32
            add hl,bc
            ld (PADR),hl
            ret
; E = byte bajo de la primera línea: borra el relleno de un jugador, las 6 columnas
; (antes solo las del ancho del cuadro anterior, y la memoria sin borrar del arranque
; salía como sprite: con la RAM a rayas del turbo R, una franja junto al jugador)
PCLR:       ld h,BUFPG
            ld c,NCOL
            xor a
.c:         ld l,e
            ld b,NLIN/4
.z:         DUP 4
            ld (hl),a
            inc l
            EDUP
            djnz .z
            inc h
            dec c
            jr nz,.c
            ret
            ASSERT $ <= 2680h

; ---- cambio de juego de sprites ----------------------------------------------------
            ORG 0EA42h              ; resto del hueco de E97Ah
; si hay un juego pendiente, se pasa a verlo (R5). Cambia A
SATSW:      ld a,(R5P)
            or a
            ret z
            out (99h),a
            ld (DISP),a
            ld a,85h
            out (99h),a
            xor a
            ld (R5P),a
            ret
; final de PFUP: lo que había (FID+1) y el cambio si no se ha hecho ya
PFDN:       ld hl,FID
            inc (hl)
            jp SATSW
            ASSERT $ <= 0EA60h


            ORG 249Ah               ; resto del item SPRA
; elige el juego que no se ve: patrones (PADR), primer sprite (SPN) y R5 pendiente
SPBANK:     ld a,(DISP)
            cp 36h
            ld hl,3C00h
            ld bc,3720h             ; B = R5, C = primer sprite (atributos en 1B80h)
            jr z,.b
            ld h,38h
            ld bc,3600h
.b:         ld a,b
            ld (R5P),a
            ld a,c
            ld (SPN),a
            ld (PADR),hl
            ld a,1
            ret
            ASSERT $ <= 24C0h

            ORG 20A0h               ; item SPRE
; fila de PFUP en que se cambia: la mitad de lo que ocupan los jugadores ahora y
; en el cuadro anterior (D = primera línea mínima, E = máxima)
SPEND:      ld de,0FF00h
            ld a,(ACT)
            ld c,a
            ld hl,PT
            ld b,2
.p:         rr c
            jr nc,.n
            ld a,(hl)
            cp d
            jr nc,.q1
            ld d,a
.q1:        cp e
            jr c,.n
            ld e,a
.n:         ld l,(PT+16)&255
            djnz .p
            jp SPEND2
            ASSERT $ <= 20C0h

            ORG 21A0h               ; item SPRF
SPEND2:     ld hl,(OLDP)            ; L = máx., H = mín. del anterior
            ld (OLDP),de
            ld a,h
            cp d
            jr nc,.q2
            ld d,a
.q2:        ld a,l
            cp e
            jr c,.q3
            ld e,a
.q3:        ld a,e
            add a,NLIN-1
            add a,d
            rra                     ; línea del medio
            rrca
            rrca
            rrca
            and 1Fh
            inc a                   ; PFUP llama con la fila siguiente
            ld (SATROW),a
            ret
            ASSERT $ <= 21C0h

; ---- marcador: atributos 02h y 03h (caras, build_rom.py) en rojo 8 y celeste 7 ---
            ORG TAB_HUD+2
            db 81h,71h

            ORG 22A0h               ; item SPRG
; B = ancho, HL = pares, DE = destino: borra la silueta de la línea en el relleno
; de los jugadores de OCC. Lo conserva todo menos A y F.
OCCL:       push ix
            push bc
            call LINEOF
            ld c,a
            ld ix,PT
            ld a,(OCC)
            rrca
            push af
            call c,OFX
            pop af
            ld ix,PT+16
            rrca
            call c,OFX
            pop bc
            pop ix
            ret
            ASSERT $ <= 22C0h

; ---- PFUP: sin el volcado completo de seguridad cada 32 cuadros (Rubén, 2026-10-24) ---
;      (and 31 -> or 1: nunca cero; comprobado con vramchk.py que no hace falta)
            ORG 0E205h
            or 1
