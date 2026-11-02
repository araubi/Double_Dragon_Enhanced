; =============================================================================
;  Dead code / data removed (verified: never executed nor read in a full
;  7-mission emulated play-through, and no reference from reachable code).
;  Filled with 00h. Must be included BEFORE dd_patches.asm (new code reuses it).
; =============================================================================
            MACRO ZAP from, to
            ORG from
            BLOCK (to)-(from)+1, 0
            ENDM
; --- page-0 MSX layer -------------------------------------------------------
            ZAP 0654h, 067Eh    ; unreferenced tape helpers + old blit entry (0676h)
            ZAP 06C9h, 06D8h    ; old 16-entry colour table (now TAB_PF, 256 entries)
            ZAP 0A45h, 0AACh    ; old per-frame HUD converter (replaced by HUDDIFF)
            ZAP 0BDCh, 0C60h    ; old HUD attribute converter + its colour tables
; --- shared block: ZX Spectrum leftovers -----------------------------------
            ZAP 0E173h, 0E18Bh  ; Kempston (IN 1Fh) and Fuller (IN 7Fh) joystick readers
            ZAP 0E194h, 0E1A3h  ; handlers for control types 1 and 5
            ZAP 0E1ACh, 0E1FFh  ; Spectrum keyboard scanner tail + key tables
            ZAP 0E200h, 0E300h  ; IM 2 vector table (interrupts are never enabled)
            ZAP 0E31Bh, 0E3D0h  ; silent beeper effects (OUT FEh had been NOP'ed)
            ZAP 0E3D2h, 0E511h  ; screen-line address table of the original blitter
            ZAP 0E628h, 0E864h  ; original Spectrum blitter (stack + LDI)
            ZAP 0EA7Dh, 0EA9Bh  ; unreachable Spectrum boot remnant (after JP EA9Ch)
            ZAP 0EAF6h, 0EF77h  ; Spectrum CONTROL MENU, redefine keys, beeper click
            ZAP 0EF85h, 0F040h  ; menu text printer + LD-BYTES remnant (CALL 0562h)
; retrato del marcador con figuras rediseñadas (FIGURAS=1): build_ram.py escribe aquí
; la copia de la cara original en E320h; sin FIGURAS el fichero está vacío
            INCLUDE "retrato.inc"
