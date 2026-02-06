QuakeFinder - IoT Seismic Node Firmware 🌍

Welcome to the **IoT Seismic Node** module of the **QuakeFinder** system.
This service is the "sensory edge" of the operation: it runs on ESP32-C3 hardware, continuously samples the accelerometer at high precision (100Hz), processes the data using digital signal processing filters, and securely triggers alerts to the cloud when seismic activity is detected.

## 📂 Project Structure

The project is organized according to the standard PlatformIO workflow to keep source code, libraries, and configurations clean.

```text
quakefinder-firmware/
├── include/                # Header files
├── lib/                    # Private project-specific libraries
├── src/                    # Main application source code (main.cpp)
├── test/                   # Unit tests (embedded)
├── .gitignore              # Git ignore rules
├── platformio.ini          # Project configuration & dependencies
└── README.md               # This file
```

## 🚀 Tech Stack

* **Language:** C++ (Arduino Framework)
* **OS/Kernel:** FreeRTOS (Dual-task architecture)
* **Hardware:** ESP32-C3 (RISC-V) + ADXL345 (MEMS Accelerometer)
* **Security:** MbedTLS (ECDSA NIST256p Signing)
* **Build System:** PlatformIO

---

## 🛠️ Getting Started

You can build and flash this firmware using **PlatformIO** (Recommended 🐜) either via the VSCode Extension or the Command Line Interface (CLI).

### Prerequisites

* **VSCode** with **PlatformIO IDE** extension installed.
* **ESP32-C3** board connected via USB.
* **ADXL345** sensor wired to I2C pins (SDA: 8, SCL: 9).

### Configuration

Before flashing, you **must** configure your credentials.
Open `src/main.cpp` and edit the "USER CONFIGURATION" section:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASS     = "YOUR_WIFI_PASSWORD";
const char* SERVER_HOST   = "api.quakefinder.io";
const int   SENSOR_ID     = 101; 
```

### Option 1: Run with VSCode (The "Chill" Way)

This is the preferred method for visual feedback and debugging.

1.  Open this folder in **VSCode**.
2.  Wait for PlatformIO to initialize (it will download toolchains automatically).
3.  Click the **PlatformIO Icon** (Alien face) on the left sidebar.
4.  Under `esp32-c3-devkitm-1`, click **Upload**.

### Option 2: CLI Execution

If you prefer the terminal or are working in a headless environment:

1.  Navigate to the project directory:
    ```bash
    cd quakefinder-firmware
    ```

2.  Install dependencies and build:
    ```bash
    pio run
    ```

3.  Upload to the device:
    ```bash
    pio run --target upload
    ```

4.  Monitor the output:
    ```bash
    pio device monitor
    ```

---

## 🧪 Testing & Verification

We believe in data integrity. Since this is an embedded system, "testing" involves verifying the sensor calibration and security handshake.

1.  **Open the Serial Monitor** (115200 baud).
2.  **Key Registration:** On the first boot, the device will generate cryptographic keys.
    ```text
    [SEC] Generazione nuova coppia di chiavi ECDSA...
    [SEC] DEVICE PUBLIC KEY (HEX): 04a23b...
    ```
    > **Note:** You must copy this Public Key and register it in your backend database, otherwise the server will reject the signed payloads.

3.  **Earthquake Simulation:** Shake the sensor gently. You should see:
    ```text
    [SENSOR] Event detected! Ratio: 2.15
    [NET] Dispatching alert to server...
    [NET] Response: {"status": "ok"}
    ```
