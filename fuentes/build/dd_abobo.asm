; =============================================================================
;  Abobo (enemy type 3: missions 1, 3A, 3B, 4 and 5B): when he finishes getting up
;  (state 32h -> anything else) and a player is right next to him, he strikes
;  and knocks the player down, as in the arcade (stops endless elbow-locking).
;  Also: per-mission data (player structs, hit routine) set at mission entry,
;  used to tell players apart from type-0 objects.
; =============================================================================
MIS_P1      EQU 1C92h           ; address of player 1 struct (player 2 = +18)
MIS_HIT     EQU 1C94h           ; hit routine of the loaded mission (IX attacker, IY target, DE entry)
ABO_PREV    EQU 1C96h           ; 3 bytes: previous state of the 3 enemy slots
ABO_RX      EQU 3               ; |dx| <= 3 columns
ABO_RY      EQU 2               ; |dy| <= 2

; --- blit entry: run the Abobo check once per frame, then the original work
            ORG NEWBLIT
            call PREBLIT

            ORG 0482h
PREBLIT:    call ABOCHK
            jp JPF                  ; Jeff's green + colour upload (dd_jeff.asm)

; ISPLAYER_IX / ISPLAYER_DE: Z if the struct is player 1 or player 2
ISPLAYER_IX:
            push de
            push ix
            pop de
            call ISPLAYER_DE
            pop de
            ret
ISPLAYER_DE:
            push hl
            ld hl,(MIS_P1)
            or a
            sbc hl,de
            jr z,.y
            ld hl,(MIS_P1)
            push bc
            ld bc,18
            add hl,bc
            pop bc
            or a
            sbc hl,de
.y:         pop hl
            ret

ABOCHK:     push ix
            push iy
            ld ix,(MIS_P1)
            ld de,36
            add ix,de               ; first enemy slot
            ld hl,ABO_PREV
            ld b,3
.slot:      push bc
            push hl
            ld a,(ix+9)
            ld c,(hl)
            ld (hl),a               ; remember state
            cp 32h
            jr z,.next              ; still getting up
            ld a,c
            cp 32h
            jr nz,.next             ; did not just get up
            ld a,(ix+15)
            cp 3
            jr nz,.next             ; not Abobo
            ld a,(ix+0)
            or a
            jr z,.next
            ld iy,(MIS_P1)
            call .try
            jr z,.next              ; hit done
            ld de,18
            add iy,de
            call .try
.next:      pop hl
            inc hl
            ld de,18
            add ix,de
            pop bc
            djnz .slot
            pop iy
            pop ix
            ret
; .try: IY = player. Z if Abobo struck.
.try:       ld a,(iy+0)
            or a
            jr z,.no
            ld a,(iy+9)
            cp 3Ch
            jr nc,.no               ; already down / being hit (3C..3F)
            cp 32h
            jr z,.no
            ld a,(iy+3)
            sub (ix+3)
            jr nc,.dx
            neg
.dx:        cp ABO_RX+1
            jr nc,.no
            ld a,(iy+4)
            sub (ix+4)
            jr nc,.dy
            neg
.dy:        cp ABO_RY+1
            jr nc,.no
            ; face the player and play the punch animation
            ld a,(iy+3)
            cp (ix+3)
            res 0,(ix+10)           ; facing right
            jr nc,.f
            set 0,(ix+10)           ; player on the left -> face left
.f:         ld (ix+9),10h
            ld (ix+8),0
            ; knock-down hit through the game's own hit routine
            ld de,ABO_ENTRY
            ld hl,.ret
            push hl
            ld hl,(MIS_HIT)
            jp (hl)
.ret:       xor a                   ; Z
            ret
.no:        or 1                    ; NZ
            ret
ABO_ENTRY:  db 0, 4, 0Ah            ; no score, 4 energy, knock-down stagger

ABOBO_END:
            ASSERT $ <= 0556h

            ORG 1CA0h
; --- mission entry thunks (first instruction of every mission at 9056h)
SETMIS:     ; A = mission 1..7
            push hl
            push de
            dec a
            add a,a
            add a,a
            ld e,a
            ld d,0
            ld hl,MISTABLE
            add hl,de
            ld e,(hl)
            inc hl
            ld d,(hl)
            inc hl
            ld (MIS_P1),de
            ld e,(hl)
            inc hl
            ld d,(hl)
            ld (MIS_HIT),de
            ld hl,ABO_PREV
            ld (hl),0
            inc hl
            ld (hl),0
            inc hl
            ld (hl),0
            pop de
            pop hl
            ret
            INCLUDE "mistable.inc"      ; generated: MISTABLE (player 1 struct, hit routine) x7
SETMIS_END:
            INCLUDE "scrollrec5.inc"
            ASSERT $ <= 1D00h

            ORG 00B0h
            INCLUDE "misthunks.inc"     ; generated: MISTHUNK1..7 + MISTABLE
            ASSERT $ <= 0100h
