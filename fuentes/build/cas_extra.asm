; Appended to the BLOAD block: installs page-0 tables/vars, then the original
; boot sequence (0559h). Reached from C368h (was JP 0559h).
            DEVICE NOSLOT64K
FORCE_PF    EQU 1C80h
FORCE_HUD   EQU 1C81h
ORIG_A8     EQU 1C90h
ORIG_SUB    EQU 1C91h
            ORG 0DB5Fh
EXTRA:      ld hl,TABS
            ld de,0100h
            ld bc,256
            ldir
            ld de,0300h
            ld bc,256
            ldir
            ld hl,P0A
            ld de,0040h
            ld bc,P0A_END-P0A
            ldir
            ld de,0400h
            ld bc,P0B_END-P0B
            ldir
            ld de,1C92h
            ld bc,P0C_END-P0C
            ldir
            ld de,1D40h
            ld bc,P0D_END-P0D
            ldir
            ld hl,IMH
            ld de,0038h
            ld bc,IMH_END-IMH
            ldir
            ld a,1
            ld (FORCE_PF),a
            ld (FORCE_HUD),a
            ld a,(0DA92h)           ; slot layout saved by the original loader
            ld (ORIG_A8),a
            ld a,(0DA93h)
            ld (ORIG_SUB),a
            jp 0559h
IMH:        push af
            in a,(99h)
            pop af
            ei
            reti
IMH_END:
TABS:       INCBIN "tab_hud.bin"
            INCBIN "tab_pf.bin"
P0A:        INCBIN "p0a.bin"
P0A_END:
P0B:        INCBIN "p0b.bin"
P0B_END:
P0C:        INCBIN "p0c.bin"
P0C_END:
P0D:        INCBIN "p0d.bin"
P0D_END:
EXTRA_END:
            SAVEBIN "cas_extra.bin",EXTRA,EXTRA_END-EXTRA
