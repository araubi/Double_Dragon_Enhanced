; =============================================================================
;  SETSLOT - switch one page (0..2) to a slot, expanded slots supported.
;  in : A = slot id (E000SSPP: bit7 expanded, bits 3-2 secondary, 1-0 primary)
;       B = page (0..2)
;  The code must not run in page B, and must not run in page 3 unless the
;  target primary slot is the one already in page 3. No stack is used while
;  page 3 is temporarily switched (to reach the target's subslot register).
;  Destroys AF, BC, DE, HL.  Interrupts must be disabled.
; =============================================================================
            MACRO SETSLOT_BODY
            ld c,a              ; C = slot id
            ld a,b
            add a,a
            ld b,a              ; B = shift = page*2
            ld a,c
            and 3
            call .shl
            ld e,a              ; E = primary << shift
            ld a,3
            call .shl
            cpl
            ld d,a              ; D = ~(3 << shift)
            bit 7,c
            jr z,.prim
            ld a,c
            rrca
            rrca
            and 3
            call .shl
            ld h,a              ; H = secondary << shift
            ld a,c
            rrca
            rrca
            and 0C0h
            ld l,a              ; L = primary << 6
            in a,(0A8h)
            ld b,a              ; B = A8 to restore
            and 3Fh
            or l
            out (0A8h),a        ; page 3 -> target primary   (no stack from here
            ld a,(0FFFFh)
            cpl
            and d
            or h
            ld (0FFFFh),a       ; secondary for page B
            ld a,b
            out (0A8h),a        ; page 3 restored              ... to here)
.prim:      in a,(0A8h)
            and d
            or e
            out (0A8h),a
            ret
.shl:       push bc
            inc b
            jr .s2
.s1:        add a,a
.s2:        djnz .s1
            pop bc
            ret
            ENDM
