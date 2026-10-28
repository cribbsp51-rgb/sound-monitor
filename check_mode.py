#!/usr/bin/env python3
from smbus2 import SMBus

ADDR = 0x48
REG_CONTROL = 0x06

bus = SMBus(1)
try:
    ctrl = bus.read_byte_data(ADDR, REG_CONTROL)
    
    # Map the register bits based on the datasheet configuration table
    modes = {0x00: "Z-Mode (Flat/Raw)", 0x02: "A-Mode (Human/Traffic)", 0x04: "C-Mode (Bass/Festival)"}
    current_setting = modes.get(ctrl, f"Unknown/Custom (0x{ctrl:02X})")
    
    print(f"CONTROL Register = 0x{ctrl:02X} -> Active Filter: {current_setting}")
except Exception as e:
    print(f"Error reading I2C bus: {e}")
finally:
    bus.close()
