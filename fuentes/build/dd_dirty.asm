; =============================================================================
;  Dirty-cell playfield upload.
;  The game already works with dirty rectangles: each frame it restores the
;  background under last frame's figures and saves+draws the new ones. The
;  figure renderer of every mission is hooked (pattern-patched at build time,
;  CALL MARK) to stamp the touched 8x8 cells with the frame id. The blit then
;  uploads only cells stamped with the current or the previous frame id
;  (new drawings + restored backgrounds). Scroll, end-of-mission fade, full
;  redraws and a safety refresh every 32 frames send the whole playfield.
; =============================================================================
DMAP        EQU 0EAF6h          ; 640 b, one byte per playfield cell (frame id)
DROW        EQU DMAP+640        ; 20 b, per char row
FID         EQU DROW+20         ; current frame id
FULLF       EQU FID+1           ; 1 = send the whole playfield this frame
FCNT        EQU FID+2           ; safety-refresh counter
            ASSERT FCNT < 0EE48h    ; EE48h+ is overwritten by mission 5B's extra block

            ORG FULLF
            db 1

; --- scroll routines (shared): whole buffer shifts -> full upload
            ORG 0E867h
            jp SCRHOOK1
            nop
            ORG 0E8D2h
            jp SCRHOOK2
            nop

; --- NEWBLIT: patterns now via PFUP instead of the full 06E9h copy
            ORG NEWBLIT
            call PFDIFF
            call PFUP

            ORG CODE_B_END
DIRTY_START:
SCRHOOK1:   push af
            ld a,1
            ld (FULLF),a
            xor a
            ld (G_PEND),a
            pop af
            push ix
            push iy
            jp 0E86Bh
SCRHOOK2:   push af
            ld a,1
            ld (FULLF),a
            xor a
            ld (G_PEND),a
            pop af
            push ix
            push iy
            jp 0E8D6h

; --- called by each mission's end-of-mission fade instead of LD HL,2C00h
FADEHOOK:   push af
            ld a,1
            ld (FULLF),a
            pop af
            ld hl,2C00h
            ret

; --- called by each mission's figure renderer (replaces 6 bytes that store the
;     destination into the save list). HL = destination in the 2C00h buffer.
;     Self-modified operands of the caller: height (lines) at ret+5, width at ret+8.
MARK:       ld a,l
            ld (de),a
            inc de
            ld a,h
            ld (de),a
            inc de
            push hl
            push de
            push bc
            ld hl,6
            add hl,sp
            ld e,(hl)
            inc hl
            ld d,(hl)               ; DE = return address
            ld (MRET),de            ; for JMARK (Jeff's colour)
            ex de,hl
            ld de,5
            add hl,de
            ld b,(hl)               ; B = height in lines
            inc hl
            inc hl
            inc hl
            ld c,(hl)               ; C = width in bytes
            ld hl,4
            add hl,sp
            ld a,(hl)
            inc hl
            ld h,(hl)
            ld l,a                  ; HL = destination
MARKCORE:                           ; HL = destination, B = lines, C = bytes (3 regs pushed)
            ld a,h
            sub 2Ch
            jr c,.out
            cp 20
            jr nc,.out
            ld d,a                  ; D = first char row
            ld a,l
            and 1Fh
            ld e,a                  ; E = first column
            ld a,b
            or a
            jr z,.out
            ld a,l
            rlca
            rlca
            rlca
            and 7                   ; first line inside the row
            add a,b
            dec a
            rrca
            rrca
            rrca
            and 1Fh
            inc a
            ld b,a                  ; B = rows spanned
            ld a,e
            add a,c
            cp 33
            jr c,.w
            ld a,32
            sub e
            ld c,a                  ; clip width at the right edge
.w:         ld a,c
            or a
            jr z,.out
            call JMARK
.row:       ld a,d
            cp 20
            jr nc,.out
            ld hl,DROW
            add a,l
            ld l,a
            jr nc,.r1
            inc h
.r1:        ld a,(FID)
            ld (hl),a
            ld l,d
            ld h,0
            add hl,hl
            add hl,hl
            add hl,hl
            add hl,hl
            add hl,hl
            push de
            ld d,0
            add hl,de               ; + column
            ld de,DMAP
            add hl,de
            pop de
            push bc
            ld b,c
.col:       ld (hl),a
            inc hl
            djnz .col
            pop bc
            inc d
            djnz .row
.out:       pop bc
            pop de
            pop hl
            ret

DIRTY_END_B:
            ASSERT $ <= 0E865h

; --- playfield pattern upload --------------------------------------------------
            ORG 0E200h
PFUP:       ld hl,FCNT
            inc (hl)
            ld a,(hl)
            and 31
            jr nz,.nf
            ld a,1
            ld (FULLF),a
.nf:        ld a,(FULLF)
            or a
            jr z,.part
            xor a
            ld (FULLF),a
            call 06E9h              ; whole playfield
            jr .done
.part:      ld a,(FID)
            ld (.c1+1),a
            ld (.c3+1),a
            dec a
            ld (.c2+1),a
            ld (.c4+1),a
            ld hl,DROW
            ld d,0
.rl:        ld a,(hl)
.c1:        cp 0
            jr z,.row
.c2:        cp 0
            jr nz,.nr
.row:       push hl
            ld l,d
            ld h,0
            add hl,hl
            add hl,hl
            add hl,hl
            add hl,hl
            add hl,hl
            ld bc,DMAP
            add hl,bc
            ld e,0
.cl:        ld a,(hl)
.c3:        cp 0
            jr z,.up
.c4:        cp 0
            jr nz,.nc
.up:        push hl
            push de
            ld a,e
            add a,a
            add a,a
            add a,a
            out (VDPC),a
            ld a,d
            add a,42h               ; VRAM 0200h + row*256, write
            out (VDPC),a
            ld a,d
            add a,2Ch
            ld h,a
            ld l,e
            ld de,32
            DUP 8
            ld a,(hl)               ; 8
            out (VDPD),a            ; 12
            add hl,de               ; 12 -> 32 T
            EDUP
            pop de
            pop hl
.nc:        inc hl
            inc e
            ld a,e
            cp 32
            jr nz,.cl
            pop hl
.nr:        inc hl
            inc d
            ld a,d
            cp 20
            jr nz,.rl
.done:      ld hl,FID
            inc (hl)
            ret
DIRTY_END:
            ASSERT $ <= 0E301h
