; =============================================================================
;  Jeff: an enemy with the players' graphics and moves.
;  The engine already shares the move code between players and enemies (the
;  enemy AI produces joystick-like commands) and picks the animation frames by
;  type (type 0 = player frames). Jeff is a type-0 struct in an enemy slot.
;  What used to mean "is a player" in the hit code (type == 0) now compares the
;  struct with the mission's player slots (ISPLAYER), so Jeff hits only the
;  players and the other enemies don't hit him. His AI also kicks.
;  Mission patches are applied by pattern in build_ram.py.
; =============================================================================
            ORG 0BDCh
JEFF_START:
; Z if IX/IY is a player; A = type (flags untouched by the LD)
ISPX:       call ISPLAYER_IX
            ld a,(ix+15)
            ret
ISPY:       push de
            push iy
            pop de
            call ISPLAYER_DE
            pop de
            ld a,(iy+15)
            ret

; Called (through JREC_n) instead of the enemy AI's call to the command routine.
; IX = enemy, A = command. For Jeff, a plain attack becomes a kick (attack
; towards the facing side) half of the time.
JEFFCMD:    ld c,a
            ld a,(ix+15)
            or a
            ld a,c
            ret nz                  ; not Jeff
            cp 10h
            ret nz
            ld a,r
            and 1
            ld a,c
            ret z
            ld a,(ix+10)
            and 1                   ; facing: 0 right, 1 left
            add a,11h               ; 11h attack right / 12h attack left
            ret
            INCLUDE "jrec.inc"      ; generated: JREC_n: call JEFFCMD / jp <command routine of mission n>
JEFF_END:
            ASSERT $ <= 0C61h

; =============================================================================
;  Jeff in dark red. The playfield colour of each 8x8 cell comes from the Spectrum
;  attribute buffer (2980h) through TAB_PF. Attribute bit 5 is never used by
;  the game, so TAB_PF maps "bit 5 set" to dark red ink. When the renderer draws
;  Jeff (hook in MARK), bit 5 is set on the cells he covers; after the colour
;  upload of the frame it is cleared again on the whole buffer.
; =============================================================================
JFLAG       EQU 0E173h          ; 1 = some attribute has bit 5 set
JT          EQU JFLAG+1         ; rectangle being drawn: col, row, cols, rows
MRET        EQU JT+4            ; MARK's return address (renderer site)
            ASSERT MRET+2 <= 0E18Ch

            ORG 1D40h               ; free gap of the HUD shadow page (low bytes 40h-BFh)
; called by MARK with D = first row, E = first column, B = rows, C = columns
JMARK:      push af
            push bc
            push de
            push hl
            ld (JT),de
            ld (JT+2),bc
            ld hl,(MRET)
            ld a,h
            or l
            jr z,.x                 ; not a figure (background tile, DMARK)
            ld de,18h               ; renderer: LD IX,descriptor at return+16h
            add hl,de
            ld e,(hl)
            inc hl
            ld d,(hl)               ; DE = descriptor of the figure being drawn
            ld hl,(MIS_P1)
            ld bc,36+5
            add hl,bc               ; first enemy slot, +5 = its descriptor
            ld b,3
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
            jr nc,.n2
            inc h
.n2:        djnz .l
.x:         pop hl
            pop de
            pop bc
            pop af
            ret
.f:         ld de,9
            add hl,de               ; +6 -> +15: type
            ld a,(hl)
            or a
            jr nz,.x                ; not Jeff
            ld a,1
            ld (JFLAG),a
            ld hl,(JT)              ; L = col, H = row
            jp JSETR
JMARK_END:
            INCLUDE "scrollrec8.inc"    ; two scroll trampoline records (see dd_gameplay.asm)
            ASSERT $ <= 1DC0h

; =============================================================================
;  Background tiles drawn during the game (the lift doors of mission 1 and the
;  other animated scenery) go straight into the playfield buffer, without the
;  figure renderer, so the dirty-cell upload missed them. The tile routine of
;  every mission now marks its 16x16 tile (DREC_n wraps its address call).
; =============================================================================
            ORG 0E1ACh
DMARK:      push hl
            push de
            push bc
            push hl
            ld hl,0
            ld (MRET),hl            ; tell JMARK this is no figure
            pop hl
            ld bc,1002h             ; 16 lines, 2 bytes
            jp MARKCORE
            INCLUDE "drec.inc"      ; generated: DREC_n: call <tile address routine> / jp DMARK
            INCLUDE "scrollrec7.inc"    ; one scroll trampoline record (see dd_gameplay.asm)
DMARK_END:
; ---- objetos (bidón, caja, roca): tras su rutina de movimiento, HL vuelve a apuntar a
;      su ficha de 7 bytes (la que se guardó con push hl al principio de la vuelta). Si
;      el objeto golpeaba a un jugador, la rutina de puntos dejaba HL = 5B02h y el código
;      de derribo escribía en 5B03-5B05h: el jugador 1 «moría» sin perder energía y
;      reaparecía en otro sitio (repetición de Rubén, 2026-10-24; ya pasaba en el original).
;      Sustituye a «bit 0,(ix+11)» tras la llamada (build_ram.py, misiones 1 a 6).
OBJHL:      ld hl,2
            add hl,sp
            ld a,(hl)
            inc hl
            ld h,(hl)
            ld l,a
            bit 0,(ix+11)
            ret
OBJHL_END:
            ASSERT $ <= 0E200h

            ORG JEFF_END
; set bit 5 on the attribute cells of rectangle JT, then back to JMARK's exit
JSETR:      ld a,h
            ld h,0
            rrca
            rrca
            rrca
            ld e,a
            and 0E0h
            or l
            ld l,a                  ; row*32 + col (low)
            ld a,e
            and 1Fh
            ld h,a
            ld de,PFBUF
            add hl,de
            ld bc,(JT+2)            ; C = cols, B = rows
            ld de,32
.r:         ld a,h
            cp 2Ch
            jr nc,.e                ; below the playfield
            push hl
            push bc
.c:         set 5,(hl)
            inc hl
            dec c
            jr nz,.c
            pop bc
            pop hl
            add hl,de
            djnz .r
.e:         jp JMARK.x
JSETR_END:
            ASSERT $ <= 0C61h

            ORG 0654h
; blit: (PREBLIT did the Abobo check) colour upload, then clear Jeff's colour
JPF:        call PFDIFF
            ld a,(JFLAG)
            or a
            ret z
            xor a
            ld (JFLAG),a
            ld hl,PFBUF
            ld bc,0002h             ; 2 x 256 + 128 = 640 cells
.l:         res 5,(hl)
            inc hl
            djnz .l
            dec c
            jr nz,.l
            ld b,128
.m:         res 5,(hl)
            inc hl
            djnz .m
            ret
JPF_END:
            ASSERT $ <= 067Fh
