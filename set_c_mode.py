#!/usr/bin/env python3

from smbus2 import SMBus

ADDR = 0x48
REG_CONTROL = 0x06

bus = SMBus(1)

# Write 0x04 to configure the frequency response filters to C-mode (FWT[1:0] = 10)
bus.write_byte_data(ADDR, REG_CONTROL, 0x04)

ctrl = bus.read_byte_data(ADDR, REG_CONTROL)

print(f"CONTROL = 0x{ctrl:02X}")

bus.close()
