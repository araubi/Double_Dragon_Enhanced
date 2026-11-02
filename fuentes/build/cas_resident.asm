; =============================================================================
;  CAS version - page-0 additions
;  The tape loader is kept. One fix: the ZX Spectrum "REWIND TO START" game
;  over (missions 2-7 without credits) asks for a tape header that does not
;  exist on the MSX tape (IX=C350h, DE=0010h) and hung forever. Now it resets
;  the MSX (original slot layout restored, JP 0000h) so the tape can be reloaded.
; =============================================================================
ORIG_A8     EQU 1C90h
ORIG_SUB    EQU 1C91h
            ORG 0556h
            jp CASLOAD
            ORG 0A45h
CASLOAD:    push ix
            pop hl
            ld a,h
            cp 0C3h
            jp nz,05B3h
            ld a,l
            cp 50h
            jp nz,05B3h
            ld a,d
            or a
            jp nz,05B3h
            ld a,e
            cp 10h
            jp nz,05B3h
            di
            ld hl,.stub
            ld de,0F300h
            ld bc,.end-.stub
            ldir
            ld a,(ORIG_A8)
            ld (0F301h),a
            ld a,(ORIG_SUB)
            ld (0F305h),a
            jp 0F300h
.stub:      ld a,0
            out (0A8h),a
            ld a,0
            ld (0FFFFh),a
            jp 0000h
.end:
            ASSERT $ <= 0AADh
