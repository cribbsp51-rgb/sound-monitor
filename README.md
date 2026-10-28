# 🔊 Acoustic & Traffic Edge-Monitor (PCBA-DBM-r3)

A professional-grade, high-speed acoustic edge-monitoring daemon built for Debian Trixie OS running on a Raspberry Pi 4. The system interfaces directly with the **PCB Artists PCBA-DBM-r3** I2C Decibel Sound Level Meter Module via its vertical JST-XH hardware lines to log environmental noise baselines, identify spikes, and compile traffic/noise telemetry data.

This project focuses on balancing long-term urban traffic noise statistics with temporary, high-impact localized noise tracking (such as stadium events and music festivals).

---

## 🛠 Hardware Architecture & Connector

The module utilizes a 4-pin vertical **JST-XH** connector profile keyed for direct wiring loops.

### Pinout Mapping Configuration

| JST Pin # | Sensor Label | Wire Color | Target Raspberry Pi 4 Header Connection | Functionality            |
| :-------: | :----------: | :--------: | :-------------------------------------- | :----------------------- |
|     1     |    `VDD`     |    Red     | Pin 1 (3.3V Power Rail)                 | Power supply input.      |
|     2     |    `GND`     |   Black    | Pin 9 (Ground Reference)                | Common ground path.      |
|     3     |    `SCL`     |   Yellow   | Pin 5 (GPIO 3 / I2C1 SCL)               | I2C Serial Clock bus line|
|     4     |    `SDA`     |   Green    | Pin 3 (GPIO 2 / I2C1 SDA)               | I2C Serial Data bus line |

---

## 🎛 Frequency Weighting Register Maps

The onboard processing microcontroller calculates one acoustic weighting matrix at a time based on configuration bits inside the Control Register. 

* **Default I2C Address:** `0x48`
* **Control Register (`REG_CONTROL`):** `0x06`
* **Frequency Weighting Selection Bits:** `FWT[1:0]` (Bits 2 and 1)

### Weighting Mode Truth Table

| Mode | `FWT[1:0]` Bits | Binary Config (Bits 7-0) | Hex Value | Target Application |
| :--- | :---: | :---: | :---: | :--- |
| **Z-Weighting** | `00` | `0000 0000` | **`0x00`** | Flat/Raw audio spectrum analysis, unweighted baselines. |
| **A-Weighting** | `01` | `0000 0010` | **`0x02`** | Human hearing curve. Default mode for long-term traffic logging. |
| **C-Weighting** | `10` | `0000 0100` | **`0x04`** | Bass/Low-frequency tracking. Ideal for music festival noise enforcement. |

> ⚠️ **Firmware Operational Behavior:** The PCBA-DBM-r3 MCU automatically self-resets to its native default layout (`0x02` A-Weighting) upon receiving initialization commands or custom sensor reset triggers via `REG_RESET` (`0x09`). 

---

## 📂 Repository Directory Structure

* `sound_monitor.py` - Main orchestration loop tracking threshold crossings, event states, and daily rollovers.
* `test_meter.py` - Hardware verification and dynamic streaming diagnostic tool.
* `check_mode.py` - Non-intrusive runtime filter scanner reading `REG_CONTROL` directly.
* `set_a_mode.py` / `set_c_mode.py` / `set_z_mode.py` - Manual mode configuration override utilities.
* `analysis/` - Windows 11 workstation analytics suite parsing synced CSV log matrices into high-resolution charts.
* `meter/` - Core driver classes interacting directly with the hardware via `smbus2`.
* `exporters/` - Telemetry storage interfaces pushing clean columns to daily CSV files and a centralized SQLite database.
* `config/` - Runtime boundary parameters (e.g., event decibel threshold constraints).
* `utils/` - Shared file logging utilities.

---

## 🚀 Execution & Verification Workflow

### 1. Identify the Active Hardware Filter State
Scan the resting register configuration without mutating its properties:
```bash
python3 ./check_mode.py
```

### 2. Manual Weighting Overrides
Force the micro-controller to switch modes before staging a specific target run:
```bash
python3 ./set_a_mode.py   # Lock into A-Mode (Traffic)
python3 ./set_c_mode.py   # Lock into C-Mode (Bass/Concert)
python3 ./set_z_mode.py   # Lock into Z-Mode (Flat Spectrum)
```

### 3. Background System Deployment
The system runs as an automated background daemon orchestrated via `systemd`. To bring the production environment online securely after setting your targeted weighting mode:
```bash
sudo systemctl start sound-monitor.service
```

Monitor live logs in real-time using the system journal:
```bash
sudo journalctl -u sound-monitor.service -f
```

## 📊 Data Analytics & Public Reporting (Windows Workstation)

Raw telemetry CSV logs can be securely synced from the Raspberry Pi edge tracker to a Windows 11 workstation for offline analytics, automated table compilation, and visualization generation.

### Workstation Directory Layout
```text
C:\noise_logs\
├── reports\                             <-- Automatically generated outputs
├── sound_evidence_2026-10-18.csv        <-- Synced edge node telemetry data
├── sound_evidence_2026-10-19.csv
└── sound_evidence_2026-10-20.csv
```

### Compiling High-Resolution Infographics
The reporting suite uses `uv` (fast Python package installer and runner) alongside `pandas` and `matplotlib` to parse the log matrix, compile statistical metrics, and format the output directly into a high-resolution `.png` chart optimized for immediate social media publication (e.g., Facebook community groups).

Execute the compilation script via **PowerShell**:
```powershell
uv run --with pandas --with matplotlib C:\analyze_noise.py "C:\noise_logs"
```

### Report Output Locations
After the execution pipeline completes, the analytics suite automatically formats, names, and exports your structured graphics:
* **Target Report Location:** `C:\noise_logs\reports\`
* **Generated Infographic File:** `facebook_noise_report_YYYY-MM-DD.png`

---

## 🤝 Community Safety & Environmental Stewardship

This framework provides an objective database layout designed to give communities transparent insight into their environments. Long-term road maps aim to combine these acoustic trackers seamlessly with portable ambient **air quality telemetry** and open-source **bicycle safety overtake detection radars** to actively protect vulnerable road users and foster safer street infrastructure.
