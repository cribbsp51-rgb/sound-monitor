#!/usr/bin/env python3

from smbus2 import SMBus

ADDR = 0x48
REG_CONTROL = 0x06

bus = SMBus(1)

# Write 0x02 to configure the frequency response filters to A-mode
# Note: If your firmware is the Pro/Advanced edition, try 0x04 if 0x02 does not alter the output
bus.write_byte_data(ADDR, REG_CONTROL, 0x02)

ctrl = bus.read_byte_data(ADDR, REG_CONTROL)

print(f"CONTROL = 0x{ctrl:02X}")

bus.close()
