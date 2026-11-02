            INCLUDE "romboot.inc"
; =============================================================================
;  MegaROM version - resident page-0 code (replaces the tape loader).
;  The game still calls 0556h (the ZX Spectrum ROM LD-BYTES address, which the
;  converter emulated). Requests are identified by IX/DE and served from ROM.
; =============================================================================
            INCLUDE "slotsw.inc"
            INCLUDE "mus_vars.inc"
            INCLUDE "musbanks.inc"      ; generado: MB_01 (presentación), MB_02, ...

; ---- variables (page 0, 1C82h..) ---------------------------------------------
SLOT_CART   EQU 1C82h
SLOT_RAM1   EQU 1C83h
SLOT_RAM2   EQU 1C84h
SAVESP      EQU 1C85h       ; 2
RC_BANK     EQU 1C87h
RC_OFS      EQU 1C88h       ; 2
RC_DEST     EQU 1C8Ah       ; 2
RC_LEN      EQU 1C8Ch       ; 2
RC_N        EQU 1C8Eh       ; 2
LSTACK      EQU 2980h       ; loader stack (2900-297F unused by the game)

; tape loader, border effects and boot sequence of the CAS version are gone
            ZAP 0556h, 0653h

            ORG 0556h
            jp ROMLOAD
; =============================================================================
            ORG 0559h
; ROMLOAD - IX = destination, DE = length (game convention). Returns A=0, CF=1.
ROMLOAD:    di
            ld (SAVESP),sp
            ld sp,LSTACK
            push ix
            pop hl
            ; --- mission stub: (EA60h, 0096h) -> stub of mission (5B13h)+1
            ld bc,0EA60h
            call CMPHL
            jr nz,.notstub
            ld a,(5B13h)
            inc a
            cp 8
            jp nc,COLD              ; after the last mission -> start again
            cp 2
            jp c,COLD
            sub 2                   ; 0..5
            ld hl,STUBTAB
            jr .item
.notstub:   ld bc,9056h
            call CMPHL
            jr nz,.notmis
            ld a,(0EA60h)           ; stub byte 0 = mission number
            cp 8
            jp nc,COLD
            cp 2
            jp c,COLD
            sub 2
            ld hl,MISTAB
            jr .item
.notmis:    ld bc,0EE48h
            call CMPHL
            jr nz,COLD              ; anything else (e.g. the Spectrum "REWIND TAPE"
                                    ; header request at C350h) -> clean restart
            ld hl,EXTRAITEM
            jr .load
.item:      ; HL = table, A = index; entries are 7 bytes
            ld c,a
            add a,a
            add a,a
            add a,a
            sub c                   ; *7
            ld e,a
            ld d,0
            add hl,de
.load:      call LOADITEM
            ld sp,(SAVESP)
            xor a
            scf
            ret

; ---- cold restart: reload shared block, sprites, mission 1 and run again ------
COLD:       di
            ld sp,LSTACK
            ld a,1
            ld (FORCE_PF),a
            ld (FORCE_HUD),a
            ld hl,BOOTITEMS
            ld b,NBOOTITEMS
.l:         push bc
            push hl
            call LOADITEM
            pop hl
            ld de,7
            add hl,de
            pop bc
            djnz .l
            ld sp,2710h             ; same as the original boot sequence
            jp 0EA60h

; ---- CMPHL: Z if HL == BC -------------------------------------------------------
CMPHL:      ld a,h
            cp b
            ret nz
            ld a,l
            cp c
            ret

; ---- LOADITEM: HL -> {bank(1), ofs(2), dest(2), len(2)} -------------------------
LOADITEM:   ld de,RC_BANK
            ld bc,7
            ldir
            jp ROMCOPY

; ---- música de presentación y menú (reproductor en el banco MUSBANK) -------------
; MUSTICK: desde el bucle del menú, un paso solo si ha empezado un cuadro nuevo
MUSTICK:    in a,(99h)
            rlca
            ret nc
            jp MUSFRM               ; un cuadro de música (rom_musica.asm)
MENUW:      call MUSTICK            ; bucle del menú (esperando ESPACIO)
            jp 0D03h
MUSOFF:     ld a,2                  ; ESPACIO: se acaba la música
            ld (MUS_ST),a
            ld hl,PSGINIT
            call PSGFX.go
.r:         ld a,0F8h               ; esperar a que se suelte ESPACIO (también es
            out (0AAh),a            ; el disparo del jugador 1)
            in a,(0A9h)
            rra
            jr nc,.r
            jp 0C7Bh
; ---- 5B: la música del menú entra al llegar a la escalera de la guarida (Rubén,
;      2026-10-22), no con Willy. C40Eh = avance del scroll de la misión (los enemigos
;      esperan a un valor de C40Eh; el grupo de la escalera, a 15h). Va antes de FRAMEHK.
SC_5B       EQU 14h
FRAME5B:    push af
            ld a,(5B13h)
            cp 7
            jr nz,.x
            ld a,(MUS_PEND)         ; primer cuadro tras cargar: C40Eh aún es el de la 5A
            or a
            jr nz,.x
            ld a,(MUS_ABO)
            or a
            jr nz,.x                ; ya ha cambiado
            ld a,(0C40Eh)
            cp SC_5B
            jr c,.x
            ld a,MB_01
            call SETSONG
            ld a,80h
            ld (MUS_ABO),a
.x:         pop af
            jp FRAMEHK
VADDR:      ld a,l                  ; VRAM: HL = dirección | 4000h
            out (99h),a
            ld a,h
            out (99h),a
            xor a
            ret
VOUT:       call VADDR              ; BC bytes de DE a la VRAM (HL)
.l:         ld a,(de)
            out (98h),a
            inc de
            dec bc
            ld a,b
            or c
            jr nz,.l
            ret
RES_A_END:
            ASSERT $ <= 0654h

            ORG 0202h
; ---- ROMCOPY: RC_LEN bytes from ROM (RC_BANK:RC_OFS) to RAM RC_DEST (pages 1-3)
ROMCOPY:
.chunk:     ld hl,(RC_LEN)
            ld a,h
            or l
            ret z
            ld b,h
            ld c,l                  ; BC = remaining
            ld de,(RC_OFS)
            ld hl,2000h
            or a
            sbc hl,de               ; room left in this 8 KB bank
            call MINBC
            ld hl,(RC_DEST)
            ld a,h
            and 3Fh
            ld d,a
            ld e,l
            ld hl,4000h
            or a
            sbc hl,de               ; room left in the destination page
            call MINBC
            ld (RC_N),bc
            ld a,(RC_DEST+1)
            and 0C0h
            cp 40h
            jr z,.page1
            ; destination in page 2/3: ROM window 6000-7FFF (page 1 = cartridge)
            ld a,(SLOT_CART)
            ld b,1
            call SETSLOT
            ld a,(RC_BANK)
            ld (6800h),a
            ld hl,(RC_OFS)
            ld de,6000h
            add hl,de
            ld de,(RC_DEST)
            ld bc,(RC_N)
            ldir
            ld a,(SLOT_RAM1)
            ld b,1
            call SETSLOT
            jr .advance
.page1:     ; destination in page 1: ROM window 8000-9FFF (page 2 = cartridge)
            ld a,(SLOT_CART)
            ld b,1
            call SETSLOT
            ld a,(RC_BANK)
            ld (7000h),a
            ld a,(SLOT_CART)
            ld b,2
            call SETSLOT
            ld a,(SLOT_RAM1)
            ld b,1
            call SETSLOT
            ld hl,(RC_OFS)
            ld de,8000h
            add hl,de
            ld de,(RC_DEST)
            ld bc,(RC_N)
            ldir
            ld a,(SLOT_RAM2)
            ld b,2
            call SETSLOT
.advance:   ld bc,(RC_N)
            ld hl,(RC_DEST)
            add hl,bc
            ld (RC_DEST),hl
            ld hl,(RC_LEN)
            or a
            sbc hl,bc
            ld (RC_LEN),hl
            ld hl,(RC_OFS)
            add hl,bc
            ld a,h
            cp 20h
            jr c,.same
            ld hl,RC_BANK
            inc (hl)
            ld hl,0
.same:      ld (RC_OFS),hl
            jp .chunk

MINBC:      push hl                 ; BC = min(BC, HL)
            or a
            sbc hl,bc
            pop hl
            ret nc
            ld b,h
            ld c,l
            ret
            ASSERT $ <= 0300h

            ORG 0040h
            INCLUDE "romitems.inc"
            ASSERT $ <= 00B0h           ; MISTHUNK1.. (misthunks.inc) empiezan en 00B0h

            ORG 0400h
SETSLOT:    SETSLOT_BODY

; ---- item tables (bank, offset, dest, length) -----------------------------------
; ---- entry from the ROM boot code (page 0 already RAM, BIOS gone) ---------------
RESBOOT:    ld sp,LSTACK
            ld hl,BOOTITEMS
            ld b,NBOOTITEMS
.l:         push bc
            push hl
            call LOADITEM
            pop hl
            ld de,7
            add hl,de
            pop bc
            djnz .l
            jp RESWAIT              ; pantalla de carga con música (0A46h)
RES_B_END:
            ASSERT $ <= 0482h       ; PREBLIT (dd_abobo.asm) empieza en 0482h

; ---- pantalla de carga: ~3 s (o hasta ESPACIO / RETURN / disparo) con música ------
;      en 0A46-0AACh, el antiguo conversor del marcador (ZAP en dd_cleanup.asm)
            ORG 0A46h
RESWAIT:    ld b,180
.w:         in a,(99h)
.v:         in a,(99h)
            rlca
            jr nc,.v                ; wait for vertical blank flag
            call MUSFRM             ; música de presentación
            ld a,0F8h
            out (0AAh),a
            in a,(0A9h)
            rra
            jr nc,.go               ; SPACE
            ld a,0F7h
            out (0AAh),a
            in a,(0A9h)
            rla
            jr nc,.go               ; RETURN
            djnz .w
.go:        ld sp,2710h
            jp 0EA60h
;---- tras "MAY YOU LIVE HAPPILY FOREVER" (ENDWAIT): el logo de la recreativa unos
;     segundos con la música del final y la partida vuelve a empezar (antes: otra vez la
;     5B). El logo (el de la pantalla de carga) se carga en 9056h, la zona de la misión,
;     que COLD vuelve a cargar.
ENDLOGO:    di
            ld sp,LSTACK
            ld hl,LOGOITEM
            call LOADITEM
            xor a                   ; sprites fuera: 1B00h = D0h
            out (99h),a
            ld a,5Bh
            out (99h),a
            ld a,0D0h
            out (98h),a
            ld hl,4000h             ; patrones
            ld de,9056h
            ld bc,1800h
            call VOUT
            ld hl,6000h             ; colores
            ld b,18h
            call VOUT
            ld hl,5800h             ; nombres: 0-255 en cada tercio
            call VADDR              ; (A = 0)
            ld b,3
.n:         out (98h),a
            nop
            inc a
            jr nz,.n
            djnz .n
            ld e,12                 ; ~5,7 s
            call DELAY
            jp COLD
            ASSERT $ <= 0AADh       ; LOGOITEM, en rom_musica.asm (tras ENDWAIT)
            ASSERT $ <= 0AADh

; ---- menú con música (MENUSTART en rom_musica.asm) ---------------------------------
            ORG MUS_BK
            db MB_01                ; la primera canción: presentación
            ORG 0C78h
            jp MENUSTART
            ORG 0D0Dh
            jp MENUW
            ORG 0D9Bh
            call MUSOFF
