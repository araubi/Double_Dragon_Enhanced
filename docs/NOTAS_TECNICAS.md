# Notas técnicas del desarrollo

Diario del proyecto: análisis del juego, cambios y fallos encontrados, en el orden en que se hicieron. Los nombres de zip son las entregas de prueba de cada paso (no se publican; la versión final está en `releases/`).

## Cómo está hecho el juego (análisis)

- El código de cada misión ocupa 9056h–E14Bh; el bloque compartido, E14Ch–F040h; el núcleo gráfico, 5B5Eh–904Dh; la capa MSX, la página 0 (0556h–1C79h).
- **Zona de juego:**
  - Búfer de patrones en 2C00h y atributos en 2980h, con formato Spectrum.
  - Color por celda de 8×8: el choque de colores viene del original.
- **Personajes:**
  - Estructuras de 18 bytes.
  - Tipos: 0 = jugador, 1 = enemigo normal, 2 = Linda (Willy en la 5B), 3 = Abobo.
  - Variante de dibujo 00h/08h: Billy/Jimmy y Abobo blanco/negro.
- **Movimientos:**
  - Jugadores y enemigos comparten el código de movimientos.
  - La IA genera órdenes tipo joystick: 1 derecha, 2 izquierda, 10h disparo…
  - Los fotogramas de animación se eligen por tipo.
- **Aparición de enemigos:**
  - Tabla de registros de 7 bytes por misión: tipo, aspecto, energía, ?, X, Y, disparador (posición de scroll o evento FAh+).
  - El límite del scroll avanza según los enemigos cargados.
- **Tabla de golpes:** compartida entre jugadores y enemigos, con una copia por misión. Cada golpe tiene puntos, daño y aturdimiento; con aturdimiento ≥ 8 el que recibe cae al suelo.
- **Abobos:** salen en las misiones 1 (dos, blanco y negro), 3A, 3B, 4 y 5B.
- **Willy:** solo en la 5B. Al morir empieza el "LET'S FIGHT" entre los jugadores.
- **Jeff:** no existía en la conversión original.

## Cambios realizados

### Velocidad y técnica
- **Velocidad:** de unos 4,8 fps a entre 1,6 y 1,9 veces más rápido por fotograma.
- **Volcado de pantalla:**
  - Solo se envían las celdas 8×8 que cambian (marcado en la rutina de figuras y en la de baldosas del decorado).
  - Color y marcador se envían por diferencias.
- **VDP:** respeta las 29 T entre accesos (mínimo 30 T; 0 violaciones).
- **Sonido:**
  - Efectos PSG que no bloquean el juego.
  - Antes, los bucles de beeper silenciados congelaban el juego.
- **Joystick 1:** R7/R15 del PSG configurados correctamente.
- **Código muerto:** unos 3,1 KB de restos del Spectrum eliminados (Kempston, menú de teclas, volcador original…).
- **MegaROM ASCII8:**
  - Arranque con detección de slots, incluidos los expandidos.
  - Cargador desde ROM y reinicio limpio.

### Jugabilidad
- **Golpes:** cada golpe suena (antes solo el primero de una serie).
- **Codazo:**
  - Tumba al primer golpe (aturdimiento 0Ah).
  - Quita 6 de energía, como dos patadas.
  - Solo afecta a los jugadores.
- **Scroll:**
  - Empieza 2 columnas antes (X ≥ 24 en vez de 26).
  - Si el scroll queda pendiente, el jugador sigue hasta el borde original.
- **Abobo:** al levantarse lanza por los aires al jugador que esté pegado a él (≤ 3 columnas).
- **Jeff, nuevo enemigo:**
  - Dibujo y movimientos de jugador: puñetazo, patada y patada en salto.
  - Va en rojo oscuro por celdas.
  - Solo pega a los jugadores.
  - Aparece en la misión 2 (bloque final, al final del mapa) y en la 4 (dos en el puente).
  - En la 5B salen tres con Willy al final del mapa (Willy se ha movido allí).

### Correcciones
- **Fin de partida:** GAME OVER sin créditos en las misiones 2–5B ya no cuelga el juego, que antes pedía rebobinar una cinta inexistente.
- **Textos:** "CAPS" → "SHIFT" en los mensajes de carga.
- **Decorados animados:** las puertas del ascensor y la pared que rompe Abobo se veían a medias con el volcado por celdas; corregido.

## Tabla de golpes (igual en las 7 misiones)

| Fila | Golpe | Puntos | Daño | Aturd. | Lo usan |
|---|---|---|---|---|---|
| 0 | Puñetazo | 05h | 2 | 2 | Jugadores, enemigos normales, Abobo, Jeff |
| 1–2 | Patada / codazo (disparo + dirección) | 0Ah | 3 | 2 | Jugadores, Jeff |
| 3 | Disparo + abajo | 0Fh | 5 | 0Ah | Solo jugadores |
| 4 | Disparo + abajo + dirección | 0Fh | 4 | 0Bh | Solo jugadores |
| 5–6 | Patada en salto | 0Ah | 4 | 0Bh | Jugadores, enemigos normales, Jeff |
| 7–10 | Armas y objetos | 14h–1Eh | 10–50 | 0Ah | Todos |

- **Fuera de la tabla:**
  - Ametralladora de Willy: 25 de daño.
  - Golpe de Abobo al levantarse: 4 de daño.
  - Codazo: 6 de daño (parche).
- **Energía:**
  - Jugadores: 150.
  - Enemigos normales: 50–70.
  - Lindas: 65–80.
  - Jeff: 80.
  - Willy: 90.
  - Abobo: 70–100.

## Opciones evaluadas

- **Personajes como sprites en MSX1:** inviable a tamaño real (límite de 4 por línea y 32 en total). Al 66 % y con una sola capa sería aceptable, pero habría que redibujar todas las animaciones.
- **Versión MSX2:**
  - **Recomendado: SCREEN 5.**
    - 16 colores por píxel, sin choque de color.
    - Figuras dibujadas con las órdenes de copia con transparencia del VDP.
    - Doble página en pantalla, fondo limpio en otra página y gráficos en la cuarta: necesita 128 KB de VRAM.
    - Scroll a saltos mediante copia de bloques, que encaja con el scroll a saltos del original.
    - Hay que redibujar los gráficos en color, y el VDP no voltea al copiar.
  - **Alternativa barata: SCREEN 4.** Reutiliza casi todo lo actual; mejora poco.
  - **Ideal con MSX2+:** SCREEN 5 con scroll horizontal suave por hardware (V9958, registros 26 y 27).
  - **Descartados:** SCREEN 6, 7 y 8, por memoria y ancho de banda.

## Pendiente / ideas

- Probar en hardware real: joystick, PSG y detección de slots.
- Comprobar si el aspecto de Abobo al pegar o caer y el del barril llevado en alto son del original o de algo nuestro. Para eso, pedir un omr del momento en que se vea.
- Jugadores con su propia tabla de golpes, si se quiere ajustar su potencia sin tocar a los enemigos.
- Maqueta de un fotograma en SCREEN 5 para valorar la versión MSX2.

## Música de presentación y menú (2026-10-21)

- Petición de araubi: poner el tema de apertura de la recreativa (VGZ suyo, YM2151) en la pantalla de presentación y en el menú principal.
- Hecho solo en la MegaROM: arreglo a 3 voces PSG con batería (`fuentes/musica/vgm2psg.py`), reproductor en el banco 24 (`mus_player.asm`) y enganches en `rom_resident.asm`. Detalles en el LEEME.
- Probado en el emulador de pruebas: suena en la carga (unos 3,6 s), sigue en el menú tras una pausa de 0,2 s, se calla al pulsar ESPACIO y las 7 cargas pasan en las tres configuraciones de slots. Detecta 60 Hz con la BIOS japonesa. Grabación en `dd_musica_presentacion_msx.mp3`.
- Falta que araubi lo oiga en openMSX y en la HB-F900.

## Controles preferidos y paso de misión (2026-10-21)

- Jugador 1: cursores + ESPACIO (o joystick); jugador 2: WASD + SHIFT. Menú actualizado.
- Al completar una misión se carga la siguiente sola: se quita la opción de repetir la misma.
- En ROM y en cinta. Probado en el emulador: teclas de los dos jugadores, las 7 cargas en las tres configuraciones de slots, la cinta con su cargador y la partida aleatoria sin cuelgues ni fallos de VDP.

## Música en las misiones (2026-10-21, solo ROM)
- Canciones de la recreativa por misión (02 misiones 1 y 4, 06 misiones 2 y 5A, 07 misiones 3A y 3B, 08 misión 5B), 04 en «COMPLETED MISSION», 09 al matar a Willy (la pantalla final espera una vuelta o el disparo). Cortadas en el punto de bucle del VGM; la 09 en su repetición.
- Compás sin interrupciones: sondeo del indicador de cuadro del VDP en el volcado, scroll, controles, bucle principal y dibujo de cada misión (`rom_musica.asm` en F400h + parches por patrón en `build_rom.py`). 100 % de pasos en el emulador; juego un 4 % más lento.
- Efectos de golpe y zap en el canal C. Entrega: `DoubleDragon_musica_misiones.zip` (ROM f657a930…, CAS sin cambios, MP3 de cada canción). Detalles en `trabajo/LEEME.md`.
- Falta que araubi lo oiga en openMSX y en el HB-F900, y que confirme qué voz lleva la melodía en cada canción (elegida por estadística, sin oírla).

## Abobo tumbado y música del último Abobo (2026-10-21, solo ROM)
- araubi: los Abobos desaparecían al caer. Causa: la ROM copiaba el bloque gráfico solo hasta 8F4Dh y el de la cinta llega a 904Dh; ahí van los gráficos de Abobo tumbado. Arreglado en `build_rom.py` (comprobado en el emulador con la ROM; la cinta no tenía el fallo).
- 03 The Entrance of Abobo the Giant al aparecer el último Abobo de la misión 1 (el blanco, registro 9680h de la tabla de enemigos), en el banco 31. Sigue hasta el fin de misión.
- Ampliado (petición de araubi): la 03 también con el Jeff de la misión 2 y los dos Abobos del final de la 3B; con Willy, la música del menú.
- araubi: la 03 entraba con el primer Abobo. Ahora el jefe se reconoce por su energía inicial (el último Abobo de la 1 sale con 5Ah, el primero con 50h).
- La 03 recupera el efecto wah (cada nota crece de volumen y entra algo baja de tono) y la sirena de la entrada va nota a nota (1/6 de semicorchea).
- Látigo: solo lo recogen Linda y los jugadores, como en la recreativa (ROM y cinta, `dd_latigo.asm`).
- Entrega: `DoubleDragon_retoques.zip` (ROM 7818006c…, CAS 4e664ca9…, MP3 de la 03). Falta que araubi lo pruebe.

## Retoques 2 (2026-10-21)
- araubi: la 03 saltaba con el primer Abobo de la 3B (el negro, 5Ah), que pasaba por 50h al recibir golpes. Ahora solo cuenta una figura nueva (la energía sube hasta la del jefe); suena con los dos Abobos blancos del final.
- La canción de cada misión empieza en el primer cuadro de juego, no en la pantalla de «HIT P1 FIRE TO BEGIN» (`MUS_PEND`).
- Agarre de los pelos y rodillazos: en la misión 2 Xortrapa exigía la misma Y exacta y casi nunca salía; quitado. Jeff no se puede agarrar en ninguna misión (`GRABCHK`); Linda y Abobo ya no se podían (ROM y cinta).
- 3A y 3B van más lentas por el dibujo de figuras (el doble que en la misión 1, también sin música). Bucle de dibujo y volteo reescritos (`dd_figuras.asm`, solo ROM): +9 a +13 % en todas las misiones, memoria y pantalla idénticas cuadro a cuadro.
- Entrega: `DoubleDragon_retoques2.zip` (ROM 58ab0aa7…, CAS d39adb3c…). Recompila idéntico desde `trabajo/fuentes`. Falta que araubi lo pruebe.

## Energías como en la recreativa (2026-10-22)

- **Qué cambia:** la energía inicial de cada enemigo es la de la recreativa (dificultad normal) × 150/64. Así la proporción con el jugador, que sigue con 150, es la del original. La tabla de golpes no cambia. Detalle y fuentes en arcade/ENERGIA_GOLPES.md.
- **Equivalencia de misiones:** carga 1 → misión 1 de la recreativa; carga 2 → 2; 3A y 3B → 3; 4, 5A y 5B → 4.

| Personaje | M1 | M2 | M3 | M4 |
|---|---|---|---|---|
| Enemigo normal (aspecto 00 / 08) | 37 / 37 | 51 / 56 | 66 | 80 |
| Linda | 28 | 37 | 47 | 56 |
| Abobo blanco / negro | 89 / 103 | | 112 / 122 | 117 / 131 |
| Abobo jefe (último de la 1; los dos del final de la 3B; el del final de la 4) | 112 | | 140 | 150 |
| Jeff | | 131 | | 150 |
| Willy | | | | 150 |

- **Dónde:** `energia()` en build_ram.py, que reescribe los registros de las tablas de enemigos (SPAWN_TAB).
- **JEFES** (rom_musica.asm) reconoce a los jefes por la energía nueva: 112, 131, 140 y 150.
- **Pruebas:** musica_flujo.py, romtest.py y casflow.py pasan.
- **Entrega:** DoubleDragon_energia_recreativa.zip; falta que araubi lo pruebe.

## Figuras de la recreativa (prototipo, 2026-10-22)

- **Qué es:** las figuras del MSX redibujadas a partir de los fotogramas de la recreativa (MAME), con el mismo formato y en el mismo sitio. Detalle en figuras/LEEME.md.
- **Prototipo 1:** Billy y Jimmy (DoubleDragon_figuras_prueba.zip).
- **Prototipo 2:** además la mitad de arriba de Williams/Roper, Linda y Abobo; piernas comunes, como en la recreativa. La cara del marcador sigue siendo la original (copia en E320h). DoubleDragon_figuras_enemigos.zip (ROM 4276ae0c…, CAS 2e4765b2…).
- **Construir:** `python3 figuras/redis.py <build>` y luego `FIGURAS=1 python3 build_rom.py` (y build_cas.py). Sin FIGURAS sale la versión de siempre (ROM ad15e1ce…, CAS f8bf092f…).
- **Pruebas:** romtest.py, casflow.py y musica_flujo.py pasan; la copia de la cara no cambia en las misiones 1–3.
- Falta que araubi lo pruebe. Sin rediseñar: Willy, Jeff y los fotogramas de llevar cosas en alto.
- **Prototipo 3:** Billy con la tabla de araubi (figuras/Movimientos Double Dragon MSX.xlsx). DoubleDragon_figuras_billy.zip (ROM 035d6bd8…, CAS 97172b16…); pruebas pasan; falta que araubi lo pruebe.
- **Prototipo 3b:** piernas alineadas con la cintura y Billy sin bate en 25-28. DoubleDragon_figuras_billy2.zip (ROM 5f30cf62…, CAS 4b880267…); pruebas pasan.
- **Prototipo 3c:** colores de Billy según la regla de araubi; enemigos originales salvo las piernas compartidas. DoubleDragon_figuras_billy3.zip (ROM 05dfd853…, CAS ee3b1353…).
- **Prototipo 3d:** piernas bien colocadas en 0-7, 38-41, 46-47. DoubleDragon_figuras_billy4.zip (ROM da164088…, CAS fe9d7f21…).
- **Decisión de araubi (2026-10-22):** el cambio de figuras se deja para una futura versión MSX2; la versión MSX vuelve a las figuras originales (la compilación normal, sin FIGURAS=1). El trabajo queda en figuras/ como referencia.

## Efectos de sonido de la recreativa (2026-10-22)

- **Qué suena y cuándo** (números de la recreativa, como los identificó araubi):
  - 00 puñetazo y 01 patada, al acertar un golpe. Por el estado del que pega: 10h es puñetazo; patadas, codazo y rodillazo suenan a patada; un golpe con objeto suena a puñetazo.
  - 02 al caer al suelo un derribado. Si se queda sin energía: 17 si es un jugador y 11 si es Linda (Willy cae como los demás).
  - 06 al empezar el golpe con el bate y 0D con el látigo. 0F al lanzar un cuchillo y 10 al pararlo de una patada.
  - 04 (bidón) y 0A (roca) cuando tocan el suelo por primera vez (paso 0Bh del arco).
  - 0C al caer al agua o a un foso, en las misiones 2 a 5B.
  - 0B en la 5A, cuando cada piedra empieza a salir de la pared y está en pantalla.
  - 16 en cada ráfaga de Willy. El "zap" del final del juego queda como efecto 18.
  - El derribo ya no tiene sonido propio: lo hace el golpe.
- **ROM:** cada efecto va cuadro a cuadro en el canal C (60 por segundo), imitando la muestra: volumen, ruido y tono.
  - Diseño en `fuentes/tools/efectos.py`, que genera `sfx_data.inc`.
  - Motor SFXSTEP en `mus_player.asm`, copiado en cada banco de música. Suena también con la música parada (MUSANY en `rom_musica.asm`).
  - Variables en 02F8-02FB.
- **Cinta:** cada efecto es un solo golpe de envolvente: ruido en el canal C y tono en el A.
  - Código en `dd_sfxcas.asm`: tabla en 0040h y rutina en 0400h. `cas_extra.asm` copia ahora desde 0040h y desde 0400h.
- **Enganches:** `dd_sonido.asm`, en E30D-E3B0. Los parches por patrón en cada misión están en `build_ram.py`.
- **Comparación:** `efectos_recreativa_vs_msx.mp3`. Suena cada efecto de la recreativa seguido del del MSX (ROM); los tiempos están en el .txt del zip.
- **Pruebas:**
  - romtest, casflow y musica_flujo pasan.
  - `fuentes/sfx/engtest.py`: la ROM toca exactamente el diseño, paso a paso.
  - Jugando en el emulador se oyen golpes, derribos, bate, látigo, cuchillo, bidón, agua y piedras. No se vieron (sin forzar) Linda muriendo, el jugador muriendo, el cuchillo parado ni la metralleta.
- **Entrega:** DoubleDragon_efectos.zip (ROM a1d51b74…, CAS fc537824…). Falta que araubi lo oiga.
- **Ojo con FIGURAS=1:** el retrato en E320h choca con estos efectos y `build_ram.py` se para. Hay que moverlo antes de volver a usar las figuras.
- **Retoques del 2026-10-22, tras oírlo araubi** (DoubleDragon_efectos2.zip, ROM 8c05f3df…, CAS 3eb478b1…):
  - El rodillazo al agarrado suena como la patada. Es el enganche KNEE, sobre `set 5,(ix+10)` de la rutina de agarre.
  - Puñetazo y patada, más secos y cortos: 7 y 8 cuadros.
  - Los enemigos que mueren usan el efecto 19, que es el del jugador más grave (×0,7). Linda mantiene el suyo y Willy también usa el 19.
  - Música del jefe (03): el bucle vuelve ahora a la entrada con la sirena, como en la recreativa (`arreglos.py`, bucle 0-192). Antes solo repetía el riff de 4 compases.

## Salto que se quedaba en la reja de la misión 2 (2026-10-22)
- araubi mandó una repetición de openMSX (.omr): al principio de la misión 2, una patada en salto junto a la reja terminaba arriba, «enganchado», y al andar a la derecha caía y moría.
- Causa (ya estaba en el original de Xortrapa): el mapa de alturas de la misión tiene 6 casillas con basura en la fila baja de la reja (`45 00 3D 75 28 28` en DF7F-DF84, en vez de `09` = pared). La de altura 4 coincidía con la base del jugador en lo alto del salto (A6FB/A26E dan por aterrizado el salto si la altura de la casilla es igual a +0), y al salir de ella, caída mortal (estado 3Eh con energía 0).
- Arreglo: build_ram.py pone esas 6 casillas a 09 (patrón «reja», solo misión 2). Con la misma partida de araubi reproducida en el emulador, el salto acaba en el suelo y sigue vivo.
- La repetición se reproduce cuadro a cuadro en nuestro emulador desde una instantánea del .omr (RAM, VRAM, registros, bancos; 50 Hz). Guiones en trabajo/fuentes/repeticion/ (msxemu.c con LINES 313 y emu_set_alt/emu_set_bank/emu_key_row).
- Entrega: DoubleDragon_reja.zip (ROM 4ab33ab8…, CAS a3da125b…).

## Música de jefe en la misión 4 (2026-10-22)
- araubi: en la misión 4 no sonaba la 03 con el Abobo. La tabla JEFES (rom_musica.asm) no tenía entrada para esa misión. Añadida `db 5, 3, 150, MB_03` (Abobo del registro 978Bh, energía 150; los Jeff del puente también tienen 150 pero son de tipo 0). musica_flujo.py lo comprueba. DoubleDragon_jefe4.zip (ROM bc7234d9…, CAS igual que el de la reja).

## 5B: música del menú en la escalera y Willy por la puerta (2026-10-22)
- araubi: la música del menú debe entrar al llegar a la escalera de la guarida, no con Willy. FRAME5B (rom_resident.asm, 0616h, antes de FRAMEHK desde E613h) pone MB_01 cuando el avance del scroll C40Eh llega a 14h (SC_5B); quitada la entrada de Willy de JEFES. musica_flujo.py lo comprueba con C40Eh 13h/14h.
- araubi: Willy salía atravesando la pared de la derecha. Al moverlo al final del mapa (scroll 31h) quedó en X 20h, que ahí es pared. Ahora sale por la puerta del arco (X 0Dh, Y FCh = baja desde arriba), y el Jeff que también salía por la pared, por X 0Bh. Comprobado con walk7d.py (repeticion/).
- Entrega: DoubleDragon_willy.zip (ROM ac65e61a…, CAS e7997ad2…), incluye la reja y el jefe de la 4.

## Golpes que sonaban tres veces y rodillazo (2026-10-24)
- araubi: puñetazos y patadas sonaban «como metralletas». Un golpe acierta en cada cuadro de su animación mientras toca (un puñetazo, en sus 4 pasos), y cada acierto volvía a empezar el efecto. HITSND (dd_sonido.asm) ahora solo suena si cambia quien pega o su acción, o si el paso no es el siguiente al del último acierto (HLAST en 0474h).
- araubi: el rodillazo seguía sin sonar. Con alguien agarrado, la patada hacia delante es el rodillazo, pero no pasa por la rutina de golpes: el agarrado (estado 3Fh) pierde 1 de energía por cuadro. KNEEB (página 0, 0462h, ROM y cinta) va en lugar del «bit 6,(ix+10)» que elige su animación (patrón «rodillazo anim» en build_ram.py) y pide el 01 al empezar cada rodillazo. El enganche KNEE anterior (A47E en la 1) es otra acción con el agarrado, se deja.
- Comprobado con knee4.py/knee5.py (agarre forzado) y hitlog2.py. Entrega: DoubleDragon_golpes.zip (ROM 01107f64…, CAS 008be65e…).

## Logo de la recreativa para MSX1 y MSX2 (prueba, 2026-10-24)
- Sacado de MAME (ddragonw, pantalla de título, t.lua; la ROM se usa con -rompath a la carpeta del zip, que MAME reconoce por CRC). Mide 234x174 a tamaño real, cabe sin escalar. En ddragonw las letras DOUBLE DRAGON son crema; la imagen de araubi las tiene plateadas, así que se recolorearon (recolor.py) siguiendo su imagen.
- Conversiones en logo/: MSX2 SCREEN 5 (16 de 512 colores, k-medias), SCREEN 8, MSX1 SCREEN 2 (2 colores por 8x1, CIELAB con más peso a la luminosidad; con y sin tramas). En SCREEN 2 se pierde parte del contorno oscuro de las letras (3 colores en 8 puntos) y los naranjas salen rojos o amarillos; un retoque a mano lo mejoraría.
- logo_msx.zip: LOGO1.SC2, LOGO1D.SC2, LOGO2.SC5, LOGO2.SC8 (BLOAD ,S) y VER.BAS. Las SC2 comprobadas con nuestro emulador; SC5/SC8 sin probar en MSX2.

## Logo con tramas en el juego (2026-10-24, DoubleDragon_logo.zip)
- araubi elige: MSX1 = LOGO1D (tramas), MSX2 = SCREEN 5 (para la futura versión MSX2, sin integrar aún).
- build/logo_sc2.bin (patrones+colores, 0x3000) sustituye a la pantalla de Xortrapa (b04.bin) como pantalla de carga en ROM y CAS.
- ROM: tras «vivieron felices» ENDWAIT salta a ENDLOGO (rom_resident.asm, 0A6C): carga LOGOITEM a 9056h, lo vuelca a VRAM (VADDR/VOUT), ~6 s con la música del final y COLD → menú (antes volvía a la misión 7).
- CAS: solo el logo de carga (no hay sitio para guardarlo al final).
- ROM sha1 0bd2732d…, CAS fc34367e…. Pruebas: romtest, casflow 14, musica_flujo TODO BIEN.
- 2026-10-24: araubi retocó el logo (logo/logo_msx1_ruben.png, 14 filas de 8 px); logo_sc2.bin rehecho desde su PNG, pantalla idéntica píxel a píxel. DoubleDragon_logo2.zip.

## Sprites de color para los jugadores (2026-10-24, DoubleDragon_sprites.zip, solo ROM)
- Petición de araubi: Billy relleno con sprite azul, Jimmy con sprite rojo y ya no en negativo; Jeff con el aspecto antiguo del jugador 2 (negativo) y sin la máscara roja.
- `build/dd_sprites.asm` (+ enganches en `dd_figuras.asm`, items SPRA-SPRD en `build_rom.py`): FIGSEL sustituye la elección DRAWM/DRAWI de cada figura; los jugadores se pintan con DRAWMC, que guarda su relleno ~(máscara|tinta) (página 1E+columna, bytes bajos 40h/70h+línea); las figuras pintadas después que caen encima le borran la silueta (DRAWMO/DRAWIO, OFQ). Al empezar el volcado (E613h) SPRUPD saca el relleno en sprites 16x16 (3 bandas x hasta 3), color 4 jugador 1 y 8 jugador 2, R1=C2h.
- Sin sprites en redibujados completos (0AADh), fundido de fin de misión y logo final. JMARK desactivado (Jeff sin rojo).
- Límites: 4 sprites por línea del TMS9918 (si los dos jugadores están a la misma altura y uno usa 3, al otro le falta un trozo); coste medido +11-20 % de tiempo por cuadro (más en la 5B con muchos enemigos).
- Memoria: huecos libres E97Ah, E828h, 0071h, relleno antes de FLIPTAB, 2440h, 2540h, 2600h, F398h; variables en 1EA0h y 1FA0h.
- CAS sin cambios (sin sitio; Jimmy sigue en negativo y Jeff en rojo). Pruebas: romtest, casflow 14, musica_flujo TODO BIEN, 0 violaciones de VDP. ROM 1175a063…
- Herramientas: trabajo/fuentes/sprites/ (sprdraw.py dibuja los sprites sobre la captura, que el emulador de pruebas no pinta; speed.py, prof.py).

### Sprites 2 (2026-10-24)
- araubi: el relleno iba al revés. Ahora el sprite cubre la tinta (lo blanco) y el papel sigue negro: contorno negro y figura azul (J1) o roja (J2). Cambio en DRAWMC de dd_sprites.asm (relleno = tinta en vez de ~(máscara|tinta)).
- DoubleDragon_sprites2.zip (ROM 38d57b2d…, CAS 77855a19… sin cambios). Muestra: sprites/sprites2_muestra.png. Hojas del jugador: sprites/prota_1a1.png.

### Sprites 3 (2026-10-24)
- Desfase al saltar: los sprites se escribían al empezar el volcado y el dibujo llegaba ~80.000 T después. Ahora hay doble juego (patrones 3800h/3C00h, atributos 1B00h/1B80h): se escribe el que no se ve y R5 (36h/37h) cambia cuando PFUP pasa por la mitad de los jugadores (PPUS en E292h; si no, al final, PFDN en E299h). Unas 5 veces menos píxeles desfasados (desf2.py). Items nuevos SPRE (20A0h) y SPRF (21A0h).
- Jugador 1 en azul claro (5); jugador 2 sigue en rojo (8).
- Marcador: cara de Jimmy ya no en negativo (BAFB de cada misión: ~flip(tinta) → flip(tinta)); caras con atributo 05 (azul claro) y 02 (TAB_HUD[02]=81h, rojo). Solo ROM.
- DoubleDragon_sprites3.zip (ROM df77c747…, CAS 77855a19… sin cambios). Muestra: sprites/sprites3_muestra.png. Velocidad igual que sprites2.

### Sprites 4 (2026-10-24)
- Jugador 1 en color 7 (celeste), sprite y cara del marcador (atributo 03h, TAB_HUD[03]=71h). DoubleDragon_sprites4.zip (ROM efb136cb…).

### Sprites 5: rendimiento (2026-10-24)
- Perfil de la misión 4 (prof5.py, hist.py): lo caro es inevitable por línea (bucle AND de la oclusión, relleno en DRAWMC, 32 bytes por sprite al VDP).
- Cambios: OCCL/OFX con IX y la línea calculada una vez (item SPRG 22A0h); PCLR borra solo las columnas usadas el cuadro anterior; marcador (HUDDIFF) compara una mitad por cuadro (HUDALT, solo ROM; el marcador tarda un cuadro más en actualizarse).
- T por cuadro misiones 1-7: sin sprites [420643, 559308, 570897, 644804, 469977, 596272, 532230]; sprites4 [487052, 650451, 664677, 771381, 534727, 671937, 618917]; sprites5 [454284, 588811, 626949, 754985, 502803, 646633, 603947] (+5 a +17 %, media ~+10 %).
- DoubleDragon_sprites5.zip (ROM c0a37899…, CAS 77855a19…).

### Sprites 6: volcado (2026-10-24)
- Quitado el volcado completo de seguridad cada 32 cuadros (solo ROM; E205h and 31 → or 1). vramchk.py: 2 × 1400 cuadros en las 7 misiones sin ninguna casilla distinta entre el buffer 2C00h y la VRAM. Quita un tirón de ~150.000 T cada 32 cuadros; de media apenas cambia.
- Colores solo en filas tocadas: NO hecho. Todos los cambios de color caen en casillas marcadas (pfchk.py), pero el 56 % de las filas están tocadas en cada cuadro y la comparación ya es barata (37 T por casilla): ahorraría ~10.000 T (1,5 %) y necesita ~80 bytes que no hay libres.
- DoubleDragon_sprites6.zip.

### Willy antes (2026-10-24)
- araubi: Willy salía demasiado al final. Ahora él y los tres Jeffs salen con el scroll en 2Fh en vez de 31h (2 pasos de 16 píxeles antes; build_ram.py, JEFF_SPAWNS de la 5B). 2Fh es el primer paso en que el arco está en pantalla: antes saldrían de la pared. X corregida +4 columnas (Willy 11h, Jeffs 0Fh, 0Eh, 14h) para que sigan saliendo por la puerta (walk7e.py, sprites/willy_2F.png). ROM y cinta.
- DoubleDragon_willy2.zip (ROM ffdfcfc3…, CAS b8575d44…), con todo lo de sprites6.

## Seto del final de la misión 1 (2026-10-24)
- araubi (repetición .omr con willy2): al final de la misión 1 un salto hacia arriba acababa encima del seto, y se quedaba allí. Ya pasaba en el original.
- Causa: la misma basura de la reja de la misión 2 (`45 00 3D 75 28 28` en DF7F-DF84) cae dentro del mapa de alturas de la misión 1 (fila 8, columnas 29-34, al final del mapa) y de la 3A (fila 7). En la 3B y la 4 cae fuera de su mapa y no se lee (mapr.py: lecturas del mapa en DF7F-DF84 por misión).
- Arreglo: build_ram.py pone esas casillas al valor de las de al lado (01 en la 1, 50 en la 3A), en ROM y cinta. Con la repetición de araubi y el parche aplicado justo antes del salto (fin2.py, PATCHAT=86.5), el salto vuelve al suelo (Y 0Bh) en vez de quedarse en Y 07h.
- Guiones en trabajo/fuentes/repeticion/seto/. DoubleDragon_seto.zip (ROM 90da0630…, CAS b6d5a073…), con todo lo de willy2.

## Enemigo que caía al vacío al final de la misión 2 (2026-10-24, DoubleDragon_caida.zip)
- Repetición de araubi (dafb990a). Los enemigos que esperan turno se mueven con el scroll
  vertical (A122h suma el desplazamiento a su Y aunque no hayan salido), así que su fila de
  salida depende de cuándo se cargaron. El segundo de la pareja final (registro 9745h) salía
  en Y 0Ah, X 1Fh: con los pies (Y+5) en la fila 15, vacío en toda la columna, y caía hasta
  morir. Es lógica del original de Xortrapa (los registros no se tocaron).
- Arreglo (dd_spawny.asm, 68 bytes en los ceros del final del módulo de la misión 2, C700h;
  enganche en 9660h, «ld (ix+0),0Ah» -> call SPAWNY): al aparecer, si en las 16 filas
  bajo los pies no hay suelo, sube al suelo más cercano (hasta 4 filas). Si hay suelo
  debajo, nada cambia. En la repetición sale en Y 08h y pelea.
- ROM 917b877c, CAS 6da48dc4. romtest, musica_flujo (TODO BIEN) y casflow (14) bien.
- Scripts en trabajo/fuentes/repeticion/caida/ (fin3.py: SLOTY/RECPOKE/M2BIN; ixt.py:
  código ejecutado con IX = una ficha; use.py: comprobar que un hueco no se usa).

## Jugador «teletransportado» al recibir un bidón (2026-10-24, DoubleDragon_bidon.zip)
- Repetición de araubi (9295d1dc), principio de la misión 2: un bidón golpea al jugador 1 y
  este reaparece en el borde con energía llena y una vida menos. Causa (también en el original
  de Xortrapa): en la vuelta de los objetos (bidón, caja, roca), la rutina de movimiento llama
  a la de golpes; la de puntos (99C7h en la misión 2) deja HL = 5B02h si el golpeador no es
  un jugador, y después el derribo del objeto (9F57h -> 9F2Bh) escribe en HL+1..3 = 5B03-5B05h.
  5B04h es «jugador 1 vivo»: el juego lo da por muerto y lo hace reaparecer.
- Arreglo: OBJHL (dd_jeff.asm, E1F0h, ROM y cinta) sustituye a «bit 0,(ix+11)» tras la
  llamada y recupera HL de la pila (push hl del principio de la vuelta). Misiones 1 a 6
  (la 7 no tiene ese código). Con la repetición: el jugador cae hacia atrás y conserva la vida.
- ROM a7a8e50c, CAS 62f13186. romtest, musica_flujo (TODO BIEN) y casflow (14) bien.

## Ruido azul en la pared de la escalera, final de la misión 2 (2026-10-25, DoubleDragon_escalera.zip)
- Captura de araubi: la pared en diagonal entre la escalera verde y el suelo salía con bloques
  azules en vez de negra. Lo causó el arreglo de la caída (SPAWNY en C700h): los «ceros sin
  uso» de C6FE-C747h del módulo 2 son el bloque negro de esa pared y el código se pintaba.
  use.py no lo vio porque solo se lee con la cámara en esa zona. NO usar C6FE-C747h.
- Arreglo nuevo de la caída, sin código añadido: en A122h (ajuste por scroll vertical) se mira
  primero si la ficha está activa y después se suma el desplazamiento a la Y (antes se sumaba
  a la Y también en las que esperan turno, y solo la X se saltaba). Así salen en la Y del
  registro (Y 00 -> aterrizan arriba, en la fila 7). Solo misión 2. SPAWNY y dd_spawny.asm
  quitados; la sección «Enemigo que caía al vacío» de arriba queda sustituida por esto.
- Probado con la repetición: los dos enemigos aterrizan arriba y pelean; la pared, negra.
  ROM 8e04d91c, CAS 19d1dbcf; romtest, musica_flujo (TODO BIEN) y casflow (14) bien.

## Retoques de araubi en los fotogramas originales (2026-10-25, DoubleDragon_fotogramas.zip)
- Hoja figuras/hojas/msx_fotogramas_retocados_ruben.png contra msx_fotogramas_originales.png
  (escala 3, figura en +1,+15 de cada casilla de 120x180; trabajo/fuentes/fotogramas/map.py).
- Hecho: 33 y 83 (tumbado por el aire) sin los restos de encima: partes 870Eh y 878Eh, solo
  suyas. dd_figfix.asm, incluido en dd_ram, dd_rom y dd_cas (cada uno monta su memoria).
- Decidido por araubi (2026-10-25): se DEJA la raya de la cintura. Motivo: la raya de la cintura de 29-32, 79-82, 109-120 y 126-127 está en las
  dos primeras líneas de las piernas compartidas (621E, 62AE, 633E, 63CE, 696Eh), que en los
  fotogramas de andar (0-3, matón, Linda, Abobo, 19...) son el final del puño. No hay memoria
  para copias (5 x 144 bytes). figuras/hojas/raya_cintura_otros.png: cómo quedarían los otros.
- ROM 52b922fd, CAS 8556b675; romtest, musica_flujo y casflow (14) bien.

## Cuelgue en la misión 5A (módulo 6; 2026-10-25, DoubleDragon_cuelgue.zip)
- Repetición de araubi (.omr f3dcb59c): el ordenador se colgaba. Causa: en el bucle de objetos
  (bidón, caja, roca...) la consulta del mapa de alturas ponía estado = altura+1 también en un
  hueco VACÍO (todo a 0 salvo la Y, que arrastra el scroll vertical). El objeto «fantasma»
  entraba en la lista de dibujo con ancho 0 y la copia del fondo (BE2Dh, LDIR con BC = 0)
  copiaba 64 KB y borraba toda la memoria. Ya en el original (las cargas 1, 3A, 3B y 5A no se
  saltan los huecos vacíos; la 2 y la 4 sí).
- Arreglo: OBJCAE (dd_patches.asm, en 0F07h: restos muertos de la rutina vieja de color del
  menú, 0F07-0F42h libres en las tres versiones) sustituye a «and a / jr z / inc a /
  ld (ix+0),a» tras la llamada; no hace nada si el alto (ix+2) es 0. build_ram.py, módulos 1-6.
- Prueba: trabajo/fuentes/repeticion/cuelgue/stress.py (desde la foto 10 de la repetición, con
  teclas al azar 400 s): antes 23 de 32 partidas colgadas, ahora 0 de 32.
- ROM 1151aedb, CAS 88df2499; romtest, musica_flujo (TODO BIEN) y casflow (14) bien.

## Piedras de la pared, misión 5A (2026-10-25, DoubleDragon_piedras.zip)
- Petición de araubi: la 5A se ralentizaba con las piedras; que empiecen al acercarse y dejen
  de salir una vez superadas.
- Causa principal: cada una de las 3 piedras (5x5 casillas de 16x16) se repintaba entera en
  cada cuadro aunque estuviera quieta (y sus casillas iban a la subida a VRAM).
- STDR (dd_controles.asm, 1DB4h; en lugar de «call B19Ch» en B124h): solo repinta cuando la
  fase cambia (contador 1-6; el orden del cuadro es restaurar fondos, piedras, guardar fondos,
  dibujar figuras, así que no quedan restos).
- STGATE (dd_patches.asm, 0F15-0F42h; en lugar de «ld a,(C84Ch)/and a/ret nz» en B0C2h): una
  piedra solo arranca con el jugador (el 1, o el 2 si el 1 no está) entre 12 columnas antes y
  7 después de su borde izquierdo; la que está a medio salir acaba siempre.
- Medido (meas.py, mismo punto y 10 s quieto): zona de piedras de ~7 a ~14 cuadros de juego
  por segundo. La zona estrecha de después (estatua con lanza, 6x8 casillas, también se repinta
  cada cuadro) ~6,6; repintarla solo al cambiar da ~7,4 pero faltan 14 bytes libres.
- Libres que quedan: 1DBFh (1 byte) y E1FD-E1FFh. 0F07-0F42h y 1DB4-1DBEh ya usados.
- ROM 69ffe537, CAS af435233; romtest, musica_flujo (TODO BIEN), casflow (14) y 24 partidas
  de stress.py sin cuelgues.

## Enemigos que iban a por el látigo (2026-10-25, DoubleDragon_latigo.zip)
- Repetición de araubi (misión 3A): un matón iba hacia el látigo aunque WHIPCHK ya no le deja
  cogerlo. La IA que elige objeto (B7A8h en el módulo 3; también en los módulos 1, 2, 4, 5 y 6)
  hacía: tipo 3 nunca, Linda solo el látigo, los demás cualquier objeto.
- Ahora (build_ram.py, «latigo ia», mismos bytes): Linda solo el látigo, tipo 3 nunca, los
  demás todo menos el látigo («tipo xor 2, por 2» < 2 solo para Linda con el látigo).
- Prueba (latigo/wh.py, desde las fotos 6-8 de la repetición): antes un tipo 1 elegía el
  látigo 30 y 108 veces; ahora 0; Linda lo sigue eligiendo.
- ROM c3f89e3f, CAS de5f7c96; romtest, musica_flujo (TODO BIEN) y casflow (14) bien.

## Música de jefe que no saltó con Jeff (2026-10-25, DoubleDragon_jefe_jeff.zip)
- Repetición de araubi (misión 2, MSX2 a 60 Hz). Jeff aparece con el último bloque (B0FAh = 3).
  El aviso del jefe (FRAMEHK, rom_musica.asm) exigía ver la figura en juego con su energía
  inicial (131) la primera vez que la miraba. FRAMEHK va una vez por fotograma de juego, y a
  Jeff le pegaron antes de esa primera mirada (quedó en 29), así que no cambió la música.
- Ahora el hueco se «arma» mientras la figura espera (estado 0) con el tipo y la energía del
  jefe (JPREV = FFh). Cuando pasa a estar en juego, la música cambia aunque ya haya perdido
  energía. Una figura del mismo tipo que esperaba con otra energía no la cambia.
- musica_flujo.py ahora hace esperar a la figura antes de sacarla y le baja la energía al salir.
  La repetición (repeticion/jeff) con el código nuevo da ABO 80h, con golpe inmediato o sin él.
- ROM d0b1ed52, CAS sin cambios (de5f7c96); romtest y musica_flujo (TODO BIEN) bien.

## Piedras de la 5A, segunda vuelta (2026-10-25, DoubleDragon_puerta_piedras.zip)
- Repetición de araubi (6eaf6def): no salió ninguna piedra. Cada hueco tiene un contador
  (B2D5-B2D7h) que sube cuando no hay scroll; la piedra sale en los pasos 1-5 tras dar la
  vuelta en 1Ch. Con STGATE el contador se quedaba parado a medias (18h) mientras el jugador
  estaba lejos, y al andar seguido solo avanzaba 3 pasos en la zona: nunca llegaba a 1Ch.
- Ahora, cuando el hueco está lejos, STGATE deja en el contador el valor de distancia (>= 13h,
  normalmente >= 1Ch): al acercarse, la vuelta llega en el primer paso y la piedra sale al
  tercero. Mismo tamaño de código (E-1-C84Bh con cpl/add en lugar de ld/dec/sub).
- Probado con la repetición (contador del tercer hueco preparado): sale la piedra y golpea
  al jugador (piedras2_muestra.png).

## Puerta del final de la misión 4 (2026-10-25, mismo zip)
- Captura de araubi: basura abajo a la derecha de la puerta abierta. El último paso de la
  animación (tabla B144h del módulo 5, 4 filas x 3 baldosas) pide la baldosa 5Dh, pero el
  juego de baldosas (C742h) acaba en la 5Ch y en D2E2h empieza otra tabla (5B0Dh): sale esa
  tabla como dibujo. Ya pasaba en el original de Xortrapa. Ahora va la 5Bh (poste derecho)
  hasta el suelo (build_ram.py, n==5; puerta_m4_muestra.png: antes / 5Bh / 57h).
- ROM e3f32527, CAS 58a15103; romtest, musica_flujo (TODO BIEN) y casflow (14) bien.

## Franja en turbo R (2026-10-27)
Vista por Xavi Sorinas en openMSX turbo R con R800: franja de rayas junto a Billy al empezar. Causa: PCLR solo borraba las columnas del ancho del cuadro anterior y la columna impar del último sprite (y todo al arrancar) conservaba la RAM inicial (FF00FF0000FF00FF en el FS-A1GT de openMSX). Arreglo: PCLR borra siempre las 6 columnas (-0,8 % de velocidad, 7,9 → 7,8 fps). DoubleDragon_turboR.zip (ROM sha1 5975641e…). Reproducido con máquina C-BIOS tipo turbo R y RAM a rayas.
