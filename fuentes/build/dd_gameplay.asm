; =============================================================================
;  Gameplay changes (hooks are pattern-patched into every mission at build time)
;   1. every hit plays the hit sound (not only the first one of a combo)
;   2. the elbow (attack opposite to the facing direction) knocks down at once
;   3. scroll starts 2 columns (16 px) before the original edge
; =============================================================================
SCROLL_R    EQU 18h             ; was: X == 1Ah  -> now X >= 18h
SCROLL_L    EQU 06h             ; was: X == 03h  -> now X <  06h
EDGE_R      EQU 1Ah             ; original edge, still reachable when the map can't scroll
EDGE_L      EQU 03h
ELB_DAMAGE  EQU 6               ; elbow: energy taken (two kicks; the table gives 3)
G_PEND      EQU 1C99h           ; scroll requests since the last real scroll (page 0)

            ORG 0ED8Dh
GAMEPLAY_START:


; --- 3. SCROLL trampolines. Each patched trigger calls a 7-byte record
;     "CALL GEN_R/GEN_L ; DW check_routine, walk_address". If the map can scroll
;     the original flow continues (scroll request). If it can't and the player
;     is not yet at the original edge, he keeps walking (jump to walk_address).
GEN_R:      ld a,0
            jr GEN
GEN_L:      ld a,1
GEN:        ld (G_MODE),a
            ex (sp),hl              ; HL -> record params, caller HL saved
            push de
            push bc
            ld e,(hl)
            inc hl
            ld d,(hl)
            inc hl
            ld (.call+1),de         ; check routine
            ld e,(hl)
            inc hl
            ld d,(hl)
            inc hl
            ld (G_WALK),de          ; walk address
            ld e,(hl)
            inc hl
            ld d,(hl)
            ld (.map+1),de          ; map-limit check of this mission/side
            pop bc
            pop de
            pop hl                  ; registers as the site had them; stack = [site]
            call ISPLAYER_IX
            jr z,.player
            ; --- enemies keep the original rule: trigger only exactly at the edge
            ld a,(G_MODE)
            or a
            ld a,(ix+3)
            jr nz,.el
            cp EDGE_R
            jr .ec
.el:        cp EDGE_L
.ec:        jr nz,.ewalk
            push hl
            ld hl,(.call+1)
            ex (sp),hl
            ret                     ; -> original check, returns to the site
.ewalk:     inc sp
            inc sp
            push hl
            ld hl,(G_WALK)
            ex (sp),hl
            ret                     ; NZ, A = X -> walk, as the original JR NZ
.player:    push hl
            push de
            push bc
.call:      call 0                  ; original check (self-modified target)
            jr z,.cant
            pop bc
            push bc
.map:       call 0                  ; can the map scroll any further?
            jr z,.cant
            ; scroll allowed, but it may stay pending (e.g. the other player
            ; holds the screen). After 3 requests without a scroll, keep walking
            ; to the original edge, where the original request is made again.
            ld a,(G_MODE)
            or a
            ld a,(ix+3)
            jr nz,.pl
            cp EDGE_R
            jr nc,.req
            jr .pc
.pl:        cp EDGE_L+1
            jr c,.req
.pc:        ld a,(G_PEND)
            cp 3
            jr nc,.pend
            inc a
            ld (G_PEND),a
.req:       or 1                    ; NZ: scroll possible (flags of the CPs above must not leak)
            pop bc
            pop de
            pop hl
            ret                     ; NZ: scroll possible -> original code continues
.pend:      xor a                   ; Z: "can't scroll" for the stop path
.cant:      push af                 ; keep the check's A/flags for the stop path
            ld a,(G_MODE)
            or a
            ld a,(ix+3)
            jr nz,.left
            cp EDGE_R
            jr nc,.stop
            jr .walk
.left:      cp EDGE_L+1
            jr c,.stop
.walk:      pop af
            pop bc
            pop de
            pop hl
            inc sp
            inc sp                  ; drop the return to the site
            ld a,(ix+3)
            or a                    ; NZ, A = X: as when the original jumped to walk
            push hl
            ld hl,(G_WALK)
            ex (sp),hl
            ret                     ; -> walk_address
.stop:      pop af
            pop bc
            pop de
            pop hl
            ret                     ; Z: original "stop" path
G_MODE:     db 0
G_WALK:     dw 0
GAMEPLAY_END:
            INCLUDE "scrollrec1.inc"
            ASSERT $ <= 0EE48h

            ORG DIRTY_END
; --- 2. ELBOW: replaces "LD A,(IX+2)" in the hit routine (IX = hit-table entry,
;     attacker struct on the stack). Players are type 0 (+15); +9 = state
;     (11h attack right, 12h attack left), +10 bit 0 = facing (1 = left).
ELB:        ld a,(ix+2)             ; original: stagger value of the move
            push hl
            push de
            push bc
            ld b,a
            ld hl,8
            add hl,sp               ; bc(0) de(2) hl(4) ret(6) attacker(8)
            ld e,(hl)
            inc hl
            ld d,(hl)
            call ISPLAYER_DE
            jr nz,.no               ; not a player
            ld hl,9
            add hl,de
            ld a,(hl)               ; state
            inc hl
            ld c,(hl)               ; flags
            cp 11h
            jr z,.r
            cp 12h
            jr nz,.no
            bit 0,c                 ; attacking left: elbow if facing right
            jr nz,.no
            jr .yes
.r:         bit 0,c                 ; attacking right: elbow if facing left
            jr z,.no
.yes:       ld b,0Ah                ; same knock-down value as the strongest moves
            ld hl,6
            add hl,sp
            ld e,(hl)
            inc hl
            ld d,(hl)               ; DE = return address (just after CALL ELB)
            ex de,hl
            ld de,-5
            add hl,de               ; -> operand of the preceding LD (dmg),A
            ld e,(hl)
            inc hl
            ld d,(hl)
            ld a,ELB_DAMAGE
            ld (de),a               ; elbow damage (the hit routine already stored the table value)
.no:        ld a,b
            pop bc
            pop de
            pop hl
            ret

ELB_END:
            ASSERT $ <= 0E301h


            ORG DIRTY_END_B
            INCLUDE "scrollrec2.inc"
            ASSERT $ <= 0E865h
            ORG 0E4E2h
            INCLUDE "scrollrec3.inc"
            ASSERT $ <= 0E512h
            ORG ELB_END
            INCLUDE "scrollrec4.inc"
            ASSERT $ <= 0E301h
            ORG 0E194h
            INCLUDE "scrollrec6.inc"
            ASSERT $ <= 0E1A4h
