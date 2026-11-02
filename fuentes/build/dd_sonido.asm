; =============================================================================
;  Efectos de sonido de la recreativa (Rubén, 2026-10-22). El juego deja el efecto
;  pendiente en (E3D1h) y E301h lo manda una vez por cuadro de juego. Ahora el número
;  es el de la recreativa:
;    00 puñetazo            01 patada              02 caer derribado
;    04 bidón rebotando     06 esfuerzo con el bate 0A roca rebotando
;    0B piedras de la pared (misión 5A)            0C caer al agua
;    0D latigazo            0F lanzar cuchillo     10 parar un cuchillo de una patada
;    11 Linda muriendo      16 metralleta          17 jugador muriendo
;    18 el "zap" del final del juego (efecto antiguo)
;    19 enemigo muriendo (el del jugador, más grave)
;  La ROM los toca cuadro a cuadro (rom_musica.asm, mus_player.asm, sfx_data.inc);
;  la cinta, con un golpe de envolvente (dd_sfxcas.asm).
;  Enganches en el código de cada misión: parches por patrón en build_ram.py.
;  Código en E30D-E3D0 (restos del beeper del Spectrum, vaciados en dd_cleanup.asm).
; =============================================================================
SFXPEND     EQU 0E3D1h

            ORG 0E30Dh
SND_START:
; ---- golpe que acierta (rutina de golpes, donde antes ponía el efecto 0 si no había
;      otro): IX = el que pega. Estado 10h = puñetazo; 11h-38h = patadas, codazo,
;      rodillazo...; un objeto (clase 0-4: arma, cuchillo, bidón, roca) suena a golpe
;      Un golpe acierta en cada cuadro de su animación mientras toca (un puñetazo, en
;      los cuatro pasos): suena solo el primero. Sigue siendo el mismo si es el mismo
;      que pega (IX bajo) con la misma acción y el paso siguiente al anterior.
HITSND:     push hl
            ld hl,HLAST
            ld a,ixl
            xor (ix+9)
            cp (hl)                 ; ¿el mismo que pega con la misma acción...
            ld (hl),a
            inc hl
            ld a,(hl)
            jr nz,.n
            inc a
            cp (ix+8)               ; ...y el paso siguiente al del último golpe?
.n:         ld a,(ix+8)
            ld (hl),a
            pop hl
            ret z                   ; sí: es el mismo golpe, ya ha sonado
            ld a,(ix+9)
            cp 11h
            ld a,0                  ; puñetazo (y objetos)
            jr c,SNDSET
            inc a                   ; patada
SNDSET:     ld (SFXPEND),a
            ret

; ---- fin de la caída de un derribado (estado 3Ch, en el suelo). Con energía: golpe
;      contra el suelo; sin ella: muere (jugador, Linda; Willy cae como los demás)
LAND:       ld (ix+8),0
            ld (ix+9),3Ch
            ld a,(ix+17)
            or a
            ld a,02h
            jr nz,SNDSET
            call ISPLAYER_IX
            ld a,17h                ; jugador
            jr z,SNDSET
            ld a,(ix+15)
            and 0Fh
            cp 2
            jr nz,.en
            ld a,(5B13h)            ; misión: en la 5B el tipo 2 es Willy
            cp 7
            ld a,11h                ; Linda
            jr nz,SNDSET
.en:        ld a,19h                ; los demás: la del jugador, más grave
            jr SNDSET

; ---- rodillazo al que está agarrado del pelo (A = cualquiera al volver)
KNEE:       set 5,(ix+10)
            ld a,01h
            jr SNDSET

; ---- objeto en vuelo (IX = objeto), en cada paso. Clase 0 bate, 1 látigo, 2 cuchillo:
;      en el primer paso empieza el golpe con el arma o el lanzamiento. Clase 3 roca,
;      4 bidón: van en arco y tocan el suelo por primera vez en el paso 0Bh
FLYHK:      inc (ix+8)
            ld a,(ix+9)
            cp 3
            jr nc,.obj
            ld a,(ix+8)
            dec a
            ret nz
            ld a,(ix+9)
            or a
            ld a,06h
            jr z,SNDSET
            ld a,(ix+9)
            dec a
            ld a,0Dh
            jr z,SNDSET
            ld a,0Fh
            jr SNDSET
.obj:       ld a,(ix+8)
            cp 0Bh
            ret nz
            ld a,(ix+9)
            cp 3
            ld a,0Ah                ; roca
            jr z,SNDSET
            ld a,04h                ; bidón
            jr SNDSET

; ---- cuchillo parado de una patada: lo que hacía el salto del original y el efecto
KKICK:      ld (ix+8),0
            ld (ix+11),0
            ld (ix+10),1
            ld a,10h
            jr SNDSET

; ---- cae por debajo del suelo (agua, fosos): una vez, al pasar a muerto
FALLW:      ld a,(ix+9)
            ld (ix+9),0FFh
            inc a
            ret z
            ld a,0Ch
SNDSET2:    ld (SFXPEND),a
            ret

; ---- misión 5A: piedras que salen de la pared. Paso 1 de las 5 de cada piedra y
;      piedra en pantalla (posición distinta de 8080h)
STONE:      ld (STONEPOS),bc
            ld a,b
            cp 80h
            ret z
            ld a,(STONEPH)
            dec a
            ret nz
            ld a,0Bh
            jr SNDSET2
STONEPOS    EQU 0B148h              ; build_ram.py comprueba estas dos direcciones
STONEPH     EQU 0B147h
SND_END:
            ASSERT $ <= 0E3D1h

; ---- rodillazo: con alguien agarrado, la patada hacia delante es el rodillazo (el
;      daño lo quita el agarrado poco a poco, sin pasar por la rutina de golpes). Va en
;      lugar de "bit 6,(ix+10)" antes de elegir su animación, en cada cuadro: suena al
;      empezar cada rodillazo (estado aún 0). Devuelve Z si no agarra, como el original.
;      Página 0, 0462-0481h: libre en la ROM (tras RESBOOT) y en la cinta (tras CASSFX).
            ORG 0462h
KNEEB:      bit 6,(ix+10)
            ret z
            push af
            ld a,(ix+9)
            or a
            jr nz,.x
            inc a                   ; 01 patada
            ld (SFXPEND),a
.x:         pop af
            ret
HLAST:      db 0, 0                 ; HITSND: último que pegó (IX bajo xor acción) y su paso
            ASSERT $ <= 0482h
