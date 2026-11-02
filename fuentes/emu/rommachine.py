"""MSX1 machine with C-BIOS + cartridge, several slot layouts."""
import os
from msx import MSX
CB=os.environ.get('CBIOS_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','ext','cbios','derived','bin')
def bios():
    return open(os.path.join(CB,'cbios_main_msx1_eu.rom'),'rb').read()+open(os.path.join(CB,'cbios_logo_msx1.rom'),'rb').read()
def machine(rom, layout='A'):
    m=MSX()
    if layout=='A':      # BIOS slot 0, cart slot 1, 64K RAM slot 3
        m.add_rom(0,0,bios(),0); m.add_ascii8(1,0,rom); m.add_ram(3,0)
    elif layout=='B':    # Philips-like: slot 3 expanded, RAM in 3-2, cart in slot 2
        m.add_rom(0,0,bios(),0); m.add_ascii8(2,0,rom); m.expanded(3); m.add_ram(3,2)
    elif layout=='C':    # cart in expanded 1-1, RAM split: pages 0-1 in slot 2, pages 2-3 in slot 3-0 (expanded)
        m.add_rom(0,0,bios(),0); m.expanded(1); m.add_ascii8(1,1,rom); m.add_ram(2,0); m.expanded(3); m.add_ram(3,0)
    m.slots(0x00)
    m.set('pc',0)
    return m
