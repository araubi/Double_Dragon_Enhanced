; =============================================================================
;  Double Dragon (Xortrapa MSX conversion) - optimisation & clean-up patches
;  Applied on top of the post-load 64 KB memory image (original_mem.bin).
;  Assembler: sjasmplus.  Shared by the CAS build and the MegaROM build.
; =============================================================================

; ---- page-0 RAM map (all verified unused by the game in emulation) ----------
TAB_HUD     EQU 0100h       ; 256 b: Spectrum attr -> MSX colour (ink<<4|paper), HUD rows
TAB_PF      EQU 0300h       ; 256 b: Spectrum attr -> MSX colour (ink only), playfield
FORCE_PF    EQU 1C80h       ; 1 = playfield colour shadow invalid -> full refresh
FORCE_HUD   EQU 1C81h       ; 1 = HUD shadow invalid -> full refresh
HSH         EQU 1D00h       ; HUD pattern shadow: page 1Dh+line, low byte = Spectrum low byte
ASH         EQU 2500h       ; HUD attribute shadow (low byte = attr low byte)
PFSH        EQU 2680h       ; playfield colour shadow, 640 b, same low-byte alignment as 2980h
PFBUF       EQU 2980h       ; game playfield attribute buffer (20x32)

; ---- I/O --------------------------------------------------------------------
VDPD        EQU 98h
VDPC        EQU 99h
PSGA        EQU 0A0h
PSGW        EQU 0A1h
PSGR        EQU 0A2h

; =============================================================================
;  Page 0: tables, variables, IM1 safety handler
; =============================================================================
            ORG TAB_HUD
            INCBIN "tab_hud.bin"
            ORG TAB_PF
            INCBIN "tab_pf.bin"
            ORG 0038h
            push af                 ; never reached (game runs with DI), kept as a safe stub
            in a,(VDPC)
            pop af
            ei
            reti
            ORG FORCE_PF
            db 1,1

; =============================================================================
;  Page-0 layer: in-place rewrites (timing-safe VRAM access, >= 29 T between OUTs)
; =============================================================================

; --- 067Fh: Spectrum attrs (HL, BC cells) -> VRAM colour (DE) with playfield table.
;     Only caller left: the full-screen redraw at 0AADh. Original tail also refreshed
;     playfield patterns (overwritten right after by 0AADh) and the HUD -> HUD kept.
            ORG 067Fh
            call 06D9h              ; set VRAM write address = DE
.cell:      ld e,(hl)
            ld d,TAB_PF>>8
            ld a,(de)
            push bc
            ld b,8
.w:         out (VDPD),a            ; 12
            nop                     ; 5
            djnz .w                 ; 14  -> 31 T
            pop bc
            inc hl
            dec bc
            ld a,b
            or c
            jr nz,.cell
            jp HUDDIFF              ; FORCE_HUD was set by the 0AADh hook -> full HUD
            ASSERT $ <= 06C9h

; --- 0AADh: full-screen redraw entry -> invalidate shadows first
            ORG 0AADh
            jp AADHOOK

; --- 0C7Bh: clear pattern + colour tables (menu / game start), timing-safe
            ORG 0C7Bh
            ld a,1
            ld (FORCE_PF),a
            ld (FORCE_HUD),a
            ld (FULLF),a
            in a,(VDPC)
            xor a
            out (VDPC),a
            ld a,40h
            out (VDPC),a            ; VRAM 0000h, write
            ld c,18h
            xor a
            call .fill
            xor a
            out (VDPC),a
            ld a,60h
            out (VDPC),a            ; VRAM 2000h, write
            ld c,18h
            ld a,11h
.fill:      ld b,0
.l:         out (VDPD),a            ; 12
            nop                     ; 5
            djnz .l                 ; 14 -> 31 T
            dec c
            jr nz,.l
            ret
            ASSERT $ <= 0CF9h

; --- 0DD4h: player-1 joystick read: fix PSG R7 (port A must be INPUT) and select port 1
            ORG 0DD4h
            jp JOYFIX

; --- 0ECDh: menu text colour writer, timing-safe (was 27 T between OUTs)
            ORG 0ECDh
            ld a,(0EC1h)
            cp 19h
            ret z
            ld de,2000h
            ld hl,(0200h)
            add hl,de
            ex de,hl
            call 06D9h              ; preserves A
            cp 18h
            jr z,.multi
            ld a,(0EC2h)
            ld b,8
.s:         out (VDPD),a
            nop
            djnz .s                 ; 31 T
.fin:       ld hl,(0200h)
            ld bc,8
            add hl,bc
            ld (0200h),hl
            ex de,hl
            jp 06D9h
.multi:     ld hl,0EC3h
            ld b,8
.m:         ld a,(hl)               ; 8
            inc hl                  ; 7
            out (VDPD),a            ; 12
            djnz .m                 ; 14 -> 41 T
            jr .fin
; ---- objetos: un hueco vacío (alto 0) no puede «caer». Tras la consulta del mapa de
;      alturas, el bucle de objetos ponía estado = altura+1 aunque el hueco estuviera
;      vacío; con ancho 0 la copia del fondo (LDIR con BC = 0) borraba toda la memoria y
;      el juego se colgaba (misión 5A, repetición de Rubén, 2026-10-25). Sustituye a
;      «and a / jr z / inc a / ld (ix+0),a» tras la llamada (build_ram.py, módulos 1 a 6).
OBJCAE:     and a
            ret z
            ld e,a
            ld a,(ix+2)
            and a
            ret z
            ld a,e
            inc a
            ld (ix+0),a
            ret
; ---- misión 5A, piedras de la pared (Rubén, 2026-10-25: «que no empiece la secuencia hasta
;      que te acerques y que dejen de salir una vez superadas»). En lugar de
;      «ld a,(C84Ch) / and a / ret nz» al principio de cada piedra (B0C2h): sale con Z si la
;      piedra se mueve en este cuadro. Una piedra a medio salir (contador < 6) acaba siempre;
;      si no, solo arranca con el jugador entre STNEAR columnas antes y STPAST después de su
;      borde izquierdo; mientras está lejos, el contador queda listo para empezar la
;      secuencia nada más acercarse (repetición de Rubén: con el contador a medias se pasaba
;      sin ver ninguna). Entra con BC = contador, D = 0, E = fin del tramo visible, L = ajuste
;      de columna (los de B19Ch). Guarda el contador en STC para STDR.
STNEAR      EQU 12
STPAST      EQU 7
STGATE:     ld a,(0C84Ch)
            and a
            ret nz
            ld a,(bc)
            ld (STC),a
            cp 6
            jp c,0A276h             ; «xor a / ret» del módulo 5A
            ld a,(0C84Bh)
            cpl
            add a,e                 ; E - 1 - C84Bh
            add a,a
            add a,l                 ; columna de la piedra en pantalla
            ld d,a
            ld a,(5B04h)            ; jugador 1 vivo: su X; si no, la del 2
            and a
            ld a,(0AEF7h)
            jr nz,.p
            ld a,(0AF09h)
.p:         sub d
            ld d,0
            add a,STNEAR
            cp STNEAR+STPAST
            jp c,0A276h
            ld (bc),a               ; lejos: contador >= 13h, la primera vez que se acerque
            ret                     ; arranca enseguida (>= 1Ch pasa a 0; NZ)
            ASSERT $ <= 0F43h

; =============================================================================
;  Shared block (E14Ch-F040h): hooks
; =============================================================================

; --- control-type jump table: only types 0 (P1) and 4 (P2) are ever used; the
;     Kempston/Fuller/Sinclair handlers are deleted, other entries -> P1 handler
            ORG 0E169h
            dw 0E1A4h, 0E1A4h, 0E1A4h
            ORG 0E171h
            dw 0E1A4h

; --- sound dispatcher: blocking silent beeper loops -> non-blocking PSG effects
            ORG 0E30Ah
            jp PSGFX

; --- blit hook: was JP 0676h
            ORG 0E625h
            jp NEWBLIT

; --- boot: IM 2 with a 257-byte vector table -> IM 1 (interrupts are never enabled)
            ORG 0EA6Dh
            im 1
            nop
            nop
            nop
            nop

; --- control-menu entry -> init PSG then the MSX menu
            ORG 0EAECh
            jp MENUHOOK

; =============================================================================
;  New code, placed in freed Spectrum leftovers (E3D2-E511, E628-E864)
; =============================================================================
            ORG 0E3D2h
CODE_A_START:

; ---- blit: playfield colours (diff) + patterns + HUD (diff) -----------------
NEWBLIT:    call PFDIFF
            call 06E9h              ; playfield patterns, original routine (30 T/byte)
            ; fall through
; ---- HUD: compare the 4 Spectrum-screen rows with a shadow copy, convert only
;      the characters that changed.
HUDDIFF:    ld a,(FORCE_HUD)
            or a
            call nz,HUDINV
            ld bc,4058h             ; B = pattern page (rows 0-1), C = attr page
            ld l,0
            call HUDHALF
            ld bc,505Ah             ; rows 22-23
            ld l,0C0h
HUDHALF:
.ch:        ld h,b
            ld e,l
            ld d,HSH>>8
            ld a,(de)
            cp (hl)
            jr nz,.diff
            DUP 7
            inc h
            inc d
            ld a,(de)
            cp (hl)
            jr nz,.diff
            EDUP
            ld d,ASH>>8
            ld h,c
            ld a,(de)
            cp (hl)
            jr nz,.diff
.next:      inc l
            ld a,l
            and 3Fh
            jr nz,.ch
            ret
.diff:      ld e,l                  ; e = char index (low byte)
            ld h,0
            add hl,hl
            add hl,hl
            add hl,hl               ; idx*8
            ld a,b
            and 10h
            add a,h
            ld h,a                  ; +1000h for rows 22-23
            push hl
            ld a,l
            out (VDPC),a
            ld a,h
            or 40h
            out (VDPC),a
            ld h,b
            ld l,e
            ld d,HSH>>8
            DUP 8
            ld a,(hl)               ; 8
            out (VDPD),a            ; 12
            ld (de),a               ; 8
            inc h                   ; 5
            inc d                   ; 5  -> 38 T
            EDUP
            pop hl
            ld a,h
            add a,20h
            ld h,a                  ; colour table address
            ld a,l
            out (VDPC),a
            ld a,h
            or 40h
            out (VDPC),a
            ld h,c
            ld l,e
            ld a,(hl)               ; Spectrum attribute
            ld d,ASH>>8
            ld (de),a
            ld l,a
            ld h,TAB_HUD>>8
            ld a,(hl)
            push bc
            ld b,8
.w:         out (VDPD),a
            nop
            djnz .w                 ; 31 T
            pop bc
            ld l,e
            jr .next

HUDINV:     xor a
            ld (FORCE_HUD),a
            ld bc,4058h
            ld l,0
            call .half
            ld bc,505Ah
            ld l,0C0h
.half:      ld h,b
            ld e,l
            ld d,HSH>>8
            DUP 8
            ld a,(hl)
            cpl
            ld (de),a
            inc h
            inc d
            EDUP
            ld h,c
            ld d,ASH>>8
            ld a,(hl)
            cpl
            ld (de),a
            inc l
            ld a,l
            and 3Fh
            jr nz,.half
            ret
CODE_A_END:
            ASSERT $ <= 0E512h

            ORG 0E628h
CODE_B_START:
; ---- playfield colours: compare 640 attrs with shadow, rewrite changed cells --
PFDIFF:     ld a,(FORCE_PF)
            or a
            call nz,PFINV
            ld hl,PFBUF
            ld de,PFSH
.loop:      DUP 8
            ld a,(de)               ; 8
            cp (hl)                 ; 8
            call nz,PFCELL          ; 11
            inc e                   ; 5
            inc l                   ; 5
            EDUP
            jr nz,.loop
            inc d
            inc h
            ld a,h
            cp 2Ch
            jr nz,.loop
            ret

PFCELL:     push hl
            push de
            push bc
            ld a,(hl)
            ld (de),a               ; update shadow
            ld c,a
            ld de,-PFBUF
            add hl,de
            add hl,hl
            add hl,hl
            add hl,hl
            ld de,2200h
            add hl,de               ; VRAM colour address of the cell
            ld a,l
            out (VDPC),a
            ld a,h
            or 40h
            out (VDPC),a
            ld d,TAB_PF>>8
            ld e,c
            ld a,(de)
            ld b,8
.w:         out (VDPD),a
            nop
            djnz .w                 ; 31 T
            pop bc
            pop de
            pop hl
            ret

PFINV:      xor a
            ld (FORCE_PF),a
            ld hl,PFBUF
            ld de,PFSH
            ld bc,640
.l:         ld a,(hl)
            cpl
            ld (de),a
            inc hl
            inc de
            dec bc
            ld a,b
            or c
            jr nz,.l
            ret

; ---- 0AADh hook --------------------------------------------------------------
AADHOOK:    ld a,1
            ld (FORCE_PF),a
            ld (FORCE_HUD),a
            ld (FULLF),a
            ld a,c                  ; original first instructions of 0AADh
            ld b,20h
            jp 0AB0h

; ---- joystick fix ---------------------------------------------------------------
JOYFIX:     ld a,7
            out (PSGA),a
            ld a,9Eh                ; B out, A IN; tone A + noise C enabled (for the SFX)
            out (PSGW),a
            ld a,15
            out (PSGA),a
            in a,(PSGR)
            and 80h                 ; keep kana LED, bit 6 = 0 -> joystick port 1
            or 3Fh                  ; pins 6/7/8 high on both ports
            out (PSGW),a
            ld a,14
            out (PSGA),a
            jp 0DE6h                ; original code: IN A,(A2h) and bit decoding

; ---- PSG sound effects (non-blocking, hardware envelope ends them) ----------
PSGFX:      jp CASSFX               ; A = efecto (dd_sonido.asm); la ROM no pasa por aquí
.go:        ld a,(hl)
            inc hl
            cp 0FFh
            ret z
            out (PSGA),a
            ld a,(hl)
            inc hl
            out (PSGW),a
            jr .go
PSGINIT:    db 7,9Eh, 8,0, 9,0, 10,0, 0FFh

MENUHOOK:   ld hl,PSGINIT
            call PSGFX.go
            jp 0C61h
CODE_B_END:
            ASSERT $ <= 0E865h
