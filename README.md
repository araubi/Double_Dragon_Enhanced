# Double Dragon Enhanced (MSX1)

Versión mejorada de la conversión MSX de **Double Dragon** hecha por Xortrapa Soft a partir de la versión de ZX Spectrum (Melbourne House, 1988). El juego original es la recreativa de Technos Japan (1987).

Va más rápida y lleva música y efectos de la recreativa. Los jugadores salen en color. También suma un enemigo nuevo y corrige muchos fallos del original.

![Formato](https://img.shields.io/badge/MSX1-MegaROM%20ASCII8%20256%20KB-blue)

## Descarga

- [`releases/DoubleDragon_ASCII8.rom`](releases/DoubleDragon_ASCII8.rom): MegaROM **ASCII8** de 256 KB con las 7 cargas (1, 2, 3A, 3B, 4, 5A y 5B) y sin esperas de cinta.
  - Funciona en cualquier MSX con 64 KB de RAM, también con slots expandidos.
  - SHA-1: `5975641ebe0a84892100918be07d936a1ab23a28`.
  - Si el emulador no detecta el mapper, hay que elegir ASCII8 a mano (en openMSX, `-romtype ASCII8`).

## Controles

| | Mover | Golpe |
|---|---|---|
| Jugador 1 | Cursores o joystick 1 | ESPACIO o botón |
| Jugador 2 | W A S D | SHIFT |

## Qué cambia

La lista completa está en [`docs/CAMBIOS.txt`](docs/CAMBIOS.txt). En resumen:

- **Velocidad:** en la misión 1, de unos 4,6 fotogramas por segundo a 7,7.
  - El volcado de pantalla solo envía las celdas que cambian.
  - Se reescribió el dibujo de las figuras.
  - Se quitaron unos 3 KB de restos del Spectrum.
- **Música y sonido de la recreativa** con el PSG:
  - Una canción por misión, la del jefe y las de misión completada y final.
  - Los efectos de golpes, armas y caídas.
  - Ningún sonido detiene ya el juego.
- **Gráficos:**
  - Billy (celeste) y Jimmy (rojo) llevan sprites de color.
  - Las caras del marcador salen en color.
  - El logo de la recreativa sirve de pantalla de carga.
  - Algunos fotogramas están retocados.
- **Jugabilidad:**
  - Enemigos con la energía de la recreativa.
  - Jeff, un enemigo nuevo que sale en las misiones 2, 4 y 5B.
  - Abobo devuelve el golpe al levantarse.
  - Codazo, agarre y látigo como en la recreativa.
  - El scroll empieza antes.
- **Fallos corregidos:**
  - Cuelgues en GAME OVER y en la misión 5A.
  - Saltos que se quedaban enganchados.
  - Enemigos que caían al vacío.
  - Joystick 1 mal configurado.
  - Accesos al VDP demasiado rápidos.
  - Una franja de rayas en turbo R.

Las notas de desarrollo, con el análisis del juego y cómo se resolvió cada fallo, están en [`docs/NOTAS_TECNICAS.md`](docs/NOTAS_TECNICAS.md).

## Compilar

El repositorio **no incluye el juego original**. Para compilar hace falta la cinta original de Xortrapa:

- Nombre: `Double Dragon (1988)(Xortrapa)(ES)[enf FX-Fernando Garcia][RUN"CAS:"].cas`
- MD5: `0a9a4bc090f110a11bf67a59bd2834df`

También hacen falta Python 3 y [sjasmplus](https://github.com/z00m128/sjasmplus) 1.24.

```sh
cd fuentes
python3 extraer_cas.py "ruta/a/la/cinta_original.cas"   # crea fuentes/dd/ con los bloques de la cinta
cd build
export SJASMPLUS=/ruta/a/sjasmplus
python3 build_rom.py    # DoubleDragon_ASCII8.rom
python3 build_cas.py    # DoubleDragon_optimizado.cas (cinta con la misma estructura de 7 cargas)
```

Con esa cinta, la ROM sale idéntica byte a byte a la de `releases/`.

### Contenido

- `fuentes/build/`: parches en ensamblador (`dd_*.asm`), código de la ROM (`rom_*.asm`), reproductor de música (`mus_player.asm` y los datos `mus_*.inc`) y scripts de construcción.
- `fuentes/emu/`: emulador MSX de pruebas en C (`msxemu.c`, con el núcleo Z80 de superzazu, licencia MIT) y las pruebas en Python que comparan el juego parcheado con el original.
- `fuentes/musica/`: conversión de la música de la recreativa (VGM) a datos PSG. Los VGM no se incluyen.
- `fuentes/tools/`: desensamblador, efectos de sonido y conversión del logo.

## Licencia y avisos

- **Código propio** (`fuentes/`): licencia MIT, ver [`LICENSE`](LICENSE). El núcleo Z80 de `fuentes/emu/z80.c` es de superzazu, también con licencia MIT ([`LICENSE_z80_superzazu.txt`](fuentes/emu/LICENSE_z80_superzazu.txt)).
- **Documentación y retoques gráficos propios:** CC BY-NC-SA 4.0, ver [`LICENSE-CC`](LICENSE-CC).
- **Lo que no cubren estas licencias:**
  - El juego original (código, gráficos, textos y música) y la ROM de `releases/`, que lo contiene. Siguen siendo de sus titulares: Technos Japan (Double Dragon), Melbourne House (versión de Spectrum) y Xortrapa Soft (conversión MSX).
  - El logo y la música de la recreativa: aquí van adaptados al MSX, pero son de Technos Japan.
- Es un homenaje sin ánimo de lucro. Si algún titular lo pide, se retira.

## Créditos

- **Double Dragon:** Technos Japan, 1987.
- **Versión de ZX Spectrum:** Melbourne House, 1988.
- **Conversión MSX:** Xortrapa Soft (FX-Fernando García).
- **Versión mejorada:** araubi (dirección, pruebas, retoques gráficos y selección de efectos). Desarrollado con Claude (Anthropic).
