; =============================================================================
;  MegaROM (ASCII8) boot code - bank 0, runs at 4000h from the cartridge.
;  Finds RAM for pages 0-2 (any slot / subslot), sets up SCREEN 2, shows the
;  original loading screen, moves the resident code into page 0 RAM and jumps
;  to it. From then on the BIOS is not used.
; =============================================================================
            DEVICE NOSLOT64K
            INCLUDE "slotsw.inc"
            INCLUDE "romboot.inc"       ; generated: B_P0_*, B_SCR_* item addresses
            INCLUDE "mus_vars.inc"
RDSLT       EQU 000Ch
WRSLT       EQU 0014h
CHPUT       EQU 00A2h
INITXT      EQU 006Ch
EXPTBL      EQU 0FCC1h
SLTTBL      EQU 0FCC5h
; page-3 scratch during boot (overwritten later by the game)
B_CART      EQU 0C000h
B_RAM0      EQU 0C001h
B_RAM1      EQU 0C002h
B_RAM2      EQU 0C003h
B_RAM3      EQU 0C004h
T_SLOT      EQU 0C005h
T_ADDR      EQU 0C006h
T_ORIG      EQU 0C008h
T_PAGE      EQU 0C009h
BC_BANK     EQU 0C00Ah
BC_OFS      EQU 0C00Bh
BC_DEST     EQU 0C00Dh
BC_LEN      EQU 0C00Fh
BC_N        EQU 0C011h
BC_VRAM     EQU 0C013h
B_HZ        EQU 0C014h
; resident symbols (page 0) - generated from the RAM image build
            INCLUDE "ressyms.inc"

            ORG 4000h
            db "AB"
            dw INIT
            dw 0,0,0
            ds 6,0

INIT:       di
            xor a
            ld (6000h),a            ; ASCII8: 4000-5FFF = bank 0 (this code)
            call FINDSLOTS
            jr nc,.ok
            call INITXT
            ld hl,MSG_RAM
.p:         ld a,(hl)
            or a
            jr z,.halt
            call CHPUT
            inc hl
            jr .p
.halt:      di
            jr .halt
.ok:        di
            call VDPINIT
            call PSGINIT_B
            ; loading screen: 1800h patterns -> 0000h, 1800h colours -> 2000h
            ld hl,ITEM_SCR
            call BLOAD_ITEM
            ld a,1
            ld (BC_VRAM),a
            ld hl,0
            ld (BC_DEST),hl
            ld hl,1800h
            ld (BC_LEN),hl
            call BCOPY
            ld hl,2000h
            ld (BC_DEST),hl
            ld hl,1800h
            ld (BC_LEN),hl
            call BCOPY
            ld a,0C0h               ; display on
            out (99h),a
            ld a,81h
            out (99h),a
            ld a,(002Bh)            ; bit 7: 1 = 50 Hz (para el ritmo de la música)
            ld (B_HZ),a
            INCLUDE "m2boot0.inc"       ; MSX2 (build_rom.py, MSX2=1): versión del MSX
            ; page 0 -> RAM, BIOS gone from here on
            ld a,(B_RAM0)
            ld b,0
            call BSETSLOT
            xor a
            ld (BC_VRAM),a
            ld hl,ITEM_P0
            call BLOAD_ITEM
            call BCOPY
            ld a,(B_HZ)
            ld (MUS_HZ),a
            ld a,(B_CART)
            ld (SLOT_CART),a
            ld a,(B_RAM1)
            ld (SLOT_RAM1),a
            ld a,(B_RAM2)
            ld (SLOT_RAM2),a
            ld a,(B_RAM2)
            ld b,2
            call BSETSLOT
            INCLUDE "m2boot.inc"        ; MSX2: código residente en FDA8h
            jp RESBOOT

MSG_RAM:    db "Double Dragon needs 64KB RAM",13,10,0
ITEM_SCR:   db SCR_BANK
            dw SCR_OFS, 0, 3000h
ITEM_P0:    db P0_BANK
            dw P0_OFS, 0, P0_LEN

; ---- BLOAD_ITEM: HL -> {bank, ofs, dest, len} into BC_* -----------------------
BLOAD_ITEM: ld de,BC_BANK
            ld bc,7
            ldir
            ret

; ---- BCOPY: ROM (BC_BANK:BC_OFS) -> RAM page 0/2/3 or VRAM, via 6000-7FFF -----
BCOPY:
.chunk:     ld hl,(BC_LEN)
            ld a,h
            or l
            ret z
            ld b,h
            ld c,l
            ld de,(BC_OFS)
            ld hl,2000h
            or a
            sbc hl,de
            call BMINBC
            ld (BC_N),bc
            ld a,(BC_BANK)
            ld (6800h),a
            ld hl,(BC_OFS)
            ld de,6000h
            add hl,de
            ld de,(BC_DEST)
            ld a,(BC_VRAM)
            or a
            jr nz,.vram
            ldir
            jr .adv
.vram:      ld a,e
            out (99h),a
            ld a,d
            and 3Fh
            or 40h
            out (99h),a
.vl:        ld a,(hl)
            out (98h),a
            inc hl
            dec bc
            ld a,b
            or c
            jr nz,.vl
.adv:       ld bc,(BC_N)
            ld hl,(BC_DEST)
            add hl,bc
            ld (BC_DEST),hl
            ld hl,(BC_LEN)
            or a
            sbc hl,bc
            ld (BC_LEN),hl
            ld hl,(BC_OFS)
            add hl,bc
            ld a,h
            cp 20h
            jr c,.same
            ld hl,BC_BANK
            inc (hl)
            ld hl,0
.same:      ld (BC_OFS),hl
            jr .chunk
BMINBC:     push hl
            or a
            sbc hl,bc
            pop hl
            ret nc
            ld b,h
            ld c,l
            ret

; ---- VDP: SCREEN 2 like BASIC "COLOR 1,1,1:SCREEN 2" ----------------------------
VDPINIT:    in a,(99h)
            ld hl,VDPREGS
            ld b,8
            ld c,80h
.r:         ld a,(hl)
            out (99h),a
            ld a,c
            out (99h),a
            inc hl
            inc c
            djnz .r
            ; clear VRAM
            xor a
            out (99h),a
            ld a,40h
            out (99h),a
            ld bc,4000h
.c:         xor a
            out (98h),a
            dec bc
            ld a,b
            or c
            jr nz,.c
            ; name table 1800h: 0..255 x 3
            xor a
            out (99h),a
            ld a,58h
            out (99h),a
            ld b,3
.n:         xor a
.n2:        out (98h),a
            inc a
            jr nz,.n2
            djnz .n
            ; sprite attribute table 1B00h: Y = D0h -> no sprites
            xor a
            out (99h),a
            ld a,5Bh
            out (99h),a
            ld a,0D0h
            out (98h),a
            ret
VDPREGS:    db 02h, 80h, 06h, 0FFh, 03h, 36h, 07h, 11h   ; R1 = 80h: display off

PSGINIT_B:  ld hl,.t
.l:         ld a,(hl)
            inc hl
            cp 0FFh
            ret z
            out (0A0h),a
            ld a,(hl)
            inc hl
            out (0A1h),a
            jr .l
.t:         db 7,9Eh, 8,0, 9,0, 10,0, 15,3Fh, 0FFh

; ---- FINDSLOTS: C = error. Uses BIOS RDSLT/WRSLT (work in all pages) -----------
FINDSLOTS:  in a,(0A8h)
            rrca
            rrca
            and 3
            call SLOTID             ; current slot of page 1 (= this cartridge)
            ld (B_CART),a
            in a,(0A8h)
            rlca
            rlca
            and 3
            ld c,a
            ld b,0
            ld hl,EXPTBL
            add hl,bc
            ld a,(hl)
            and 80h
            or c
            jp p,.p3
            ld hl,SLTTBL
            add hl,bc
            ld a,(hl)
            rlca
            rlca
            and 3
            add a,a
            add a,a
            or c
            or 80h
.p3:        ld (B_RAM3),a
            ld a,80h                ; page 2
            call FINDRAM
            ret c
            ld (B_RAM2),a
            ld a,40h                ; page 1
            call FINDRAM
            ret c
            ld (B_RAM1),a
            xor a                   ; page 0
            call FINDRAM
            ret c
            ld (B_RAM0),a
            or a
            ret

; A = primary slot of page 1 -> full slot id using EXPTBL/SLTTBL
SLOTID:     ld c,a
            ld b,0
            ld hl,EXPTBL
            add hl,bc
            ld a,(hl)
            and 80h
            or c
            ret p
            ld hl,SLTTBL
            add hl,bc
            ld a,(hl)
            rrca
            rrca
            and 3
            add a,a
            add a,a
            or c
            or 80h
            ret

; FINDRAM: A = page base high byte (00/40/80). Out: A = slot id, CF = not found.
; Tries the page-3 RAM slot first, then every slot/subslot.
FINDRAM:    ld (T_PAGE),a
            ld a,(B_RAM3)
            call TESTRAM
            ld a,(T_SLOT)
            ret z
            ld c,0                  ; primary
.prim:      ld b,0
            ld hl,EXPTBL
            ld e,c
            ld d,0
            add hl,de
            ld a,(hl)
            and 80h
            jr nz,.exp
            ld a,c
            push bc
            call TESTRAM
            pop bc
            ld a,(T_SLOT)
            ret z
            jr .nextp
.exp:       ld b,0                  ; secondary
.sub:       ld a,b
            add a,a
            add a,a
            or c
            or 80h
            push bc
            call TESTRAM
            pop bc
            ld a,(T_SLOT)
            ret z
            inc b
            ld a,b
            cp 4
            jr nz,.sub
.nextp:     inc c
            ld a,c
            cp 4
            jr nz,.prim
            scf
            ret

; TESTRAM: A = slot id; tests (T_PAGE)*256+10h. Z = RAM.
TESTRAM:    ld (T_SLOT),a
            ld a,(T_PAGE)
            ld h,a
            ld l,10h
            ld (T_ADDR),hl
            ld a,(T_SLOT)
            call RDSLT
            ld (T_ORIG),a
            cpl
            ld e,a
            ld a,(T_SLOT)
            ld hl,(T_ADDR)
            call WRSLT
            ld a,(T_SLOT)
            ld hl,(T_ADDR)
            call RDSLT
            ld b,a
            ld a,(T_ORIG)
            cpl
            cp b
            push af
            ld a,(T_ORIG)
            ld e,a
            ld a,(T_SLOT)
            ld hl,(T_ADDR)
            call WRSLT
            pop af
            ret

BSETSLOT:   SETSLOT_BODY

            ASSERT $ <= 6000h
            SAVEBIN "rom_bank0.bin",4000h,2000h
