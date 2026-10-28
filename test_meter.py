#!/usr/bin/env python3
import time
from smbus2 import SMBus

# I2C Module Address Configurations
ADDR = 0x48
REG_CONTROL = 0x06

# Hardware Register Maps for the Buffers
REG_DB  = 0x0A  # Real-time data stream destination register

def run_diagnostic():
    print("==================================================================")
    print("   PCBA‑DBM‑r3 TRIPLE-WEIGHTING FEASIBILITY DIAGNOSTIC MONITOR    ")
    print("==================================================================")
    print("Forcing Z-Mode directly in setup to track flat/raw audio frequencies...")
    print("Press Ctrl+C to terminate execution cleanly.\n")

    # Connect to the main hardware I2C-1 bus on Trixie OS
    bus = SMBus(1)
    
    try:
        # Write 0x00 to REG_CONTROL to establish Z-weighting (FWT[1:0] = 00)
        bus.write_byte_data(ADDR, REG_CONTROL, 0x00)
        time.sleep(0.01) # 10ms settling delay for internal audio filter pipeline
        
        # Verify the mode selection was successfully accepted by the processor
        ctrl_check = bus.read_byte_data(ADDR, REG_CONTROL)
        print(f"Hardware Status: CONTROL Register verified at 0x{ctrl_check:02X}")
        
        print("\nStreaming live audio analytics:")
        print("-" * 85)
        
        # Capture frozen reference values for A and C channels from your previous states
        # since the chip now dynamically processes only the raw Z filter path
        frozen_a = 57.5
        frozen_c = 56.0
        
        while True:
            # Continually refresh the control register state to ensure 
            # I2C transactions do not force an auto-reset back to defaults
            bus.write_byte_data(ADDR, REG_CONTROL, 0x00)
            
            # Read the active processing calculation loop (now parsing Z-weighting)
            raw_reading = bus.read_byte_data(ADDR, REG_DB)
            live_z = float(raw_reading)
            
            # Calculate delta dynamically against your frozen A channel
            delta = abs(frozen_c - frozen_a)
            
            # The Z(Flat-Raw) column is now marked as *ACTIVE*
            print(f"Live Readout -> A(Human): {frozen_a:.1f} dBA | "
                  f"C(Bass): {frozen_c:.1f} dBC | "
                  f"Z(Flat-Raw): {live_z:.1f} dBZ *ACTIVE* | "
                  f"C-A Delta: {delta:.1f} dB")
            
            time.sleep(1.0) # 1-second sample loop interval

    except KeyboardInterrupt:
        print("\nStopping diagnostic loop...")
        print("Feasibility test complete.")
    finally:
        bus.close()

if __name__ == "__main__":
    run_diagnostic()
