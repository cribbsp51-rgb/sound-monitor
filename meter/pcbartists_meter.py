# meter/pcbartists_meter.py
from smbus2 import SMBus
import time

I2C_ADDR = 0x48

# ============================
# PCBA‑DBM‑r3.1 REGISTER MAP
# ============================

REG_SPL_A_INT       = 0x0A     # Instantaneous SPL(A)
REG_SPL_MIN         = 0x0B     # Minimum SPL(A) since last reset
REG_SPL_MAX         = 0x0C     # Maximum SPL(A) since last reset

REG_RESET           = 0x09     # Control register for clearing MIN/MAX/History/LAeq
RESET_MINMAX        = 0x02
RESET_HISTORY       = 0x04
RESET_LAEQ          = 0x06

REG_HISTORY_START   = 0x20     # Rolling SPL history buffer
HISTORY_LENGTH      = 32       # 32 samples (firmware default)


class PCBArtistsMeter:
    def __init__(self, bus=1, addr=I2C_ADDR):
        self.bus_idx = bus
        self.addr = addr
        self.bus = None

    # ------------------------------------------------------------
    # Context Manager (opens/closes I²C bus)
    # ------------------------------------------------------------
    def __enter__(self):
        self.bus = SMBus(self.bus_idx)

        # Allow sensor MCU to fully boot (critical)
        time.sleep(0.30)

        # Clear MIN/MAX after power‑up (manufacturer recommendation)
        self._robust_clear_minmax()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.bus:
            try:
                self.bus.close()
            except Exception:
                pass

    # ------------------------------------------------------------
    # Robust MIN/MAX clear with retry + verification
    # ------------------------------------------------------------
    def _robust_clear_minmax(self):
        try:
            self.bus.write_byte_data(
                self.addr,
                REG_RESET,
                RESET_MINMAX
            )
            time.sleep(0.05)

#            print(
#                f"MIN/MAX clear sent -> "
#                f"MIN={self.spl_min():.0f} "
#                f"MAX={self.spl_max():.0f}"
#        )

        except Exception:
            self._recover_i2c()

    # ------------------------------------------------------------
    # Core SPL Reads
    # ------------------------------------------------------------
    def spl(self):
        """Instantaneous A‑weighted SPL (dB)."""
        try:
            return float(self.bus.read_byte_data(self.addr, REG_SPL_A_INT))
        except OSError:
            self._recover_i2c()
            return float(self.bus.read_byte_data(self.addr, REG_SPL_A_INT))

    def spl_min(self):
        """Minimum SPL(A) since last reset."""
        try:
            return float(self.bus.read_byte_data(self.addr, REG_SPL_MIN))
        except OSError:
            self._recover_i2c()
            return float(self.bus.read_byte_data(self.addr, REG_SPL_MIN))

    def spl_max(self):
        """Maximum SPL(A) since last reset."""
        try:
            return float(self.bus.read_byte_data(self.addr, REG_SPL_MAX))
        except OSError:
            self._recover_i2c()
            return float(self.bus.read_byte_data(self.addr, REG_SPL_MAX))

    # ------------------------------------------------------------
    # History Buffer
    # ------------------------------------------------------------
    def get_history_array(self):
        """Returns rolling 32‑sample SPL(A) history."""
        try:
            return self.bus.read_i2c_block_data(self.addr, REG_HISTORY_START, HISTORY_LENGTH)
        except OSError:
            self._recover_i2c()
            return self.bus.read_i2c_block_data(self.addr, REG_HISTORY_START, HISTORY_LENGTH)

    # ------------------------------------------------------------
    # Reset / Clear Functions
    # ------------------------------------------------------------
    def clear_minmax(self):
        """Clears MIN/MAX registers."""
        self._robust_clear_minmax()

    def clear_history(self):
        """Clears rolling SPL history buffer."""
        try:
            self.bus.write_byte_data(self.addr, REG_RESET, RESET_HISTORY)
        except OSError:
            self._recover_i2c()
            self.bus.write_byte_data(self.addr, REG_RESET, RESET_HISTORY)

    def clear_la_eq(self):
        """Clears LAeq accumulator."""
        try:
            self.bus.write_byte_data(self.addr, REG_RESET, RESET_LAEQ)
        except OSError:
            self._recover_i2c()
            self.bus.write_byte_data(self.addr, REG_RESET, RESET_LAEQ)

    # ------------------------------------------------------------
    # I²C Recovery
    # ------------------------------------------------------------
    def _recover_i2c(self):
        """Auto‑recover I²C bus after transient sensor resets."""
        time.sleep(0.05)
        try:
            self.bus.close()
        except Exception:
            pass
        self.bus = SMBus(self.bus_idx)
