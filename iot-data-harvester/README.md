# iot-data-harvester 📡

Firmware for the edge sensor nodes. These devices capture acceleration data and transmit it securely to the backend.

## 🛠 Hardware & Stack
* **MCU:** ESP32-C3 SuperMini (RISC-V)
* **Sensor:** ADXL345 (Accelerometer)
* **Framework:** Arduino / PlatformIO
* **Protocol:** HTTP POST (JSON)
* **Security:** ECDSA (secp256r1/NIST256p) Signing

## ⚙️ Configuration

1.  Rename `.env.example` (or `secrets.h`) to the active configuration file required by your implementation.
2.  Populate the following fields:
    * `WIFI_SSID` / `WIFI_PASS`: Network credentials.
    * `SERVER_HOST`: IP address of the Backend.
    * `PRIVATE_KEY_HEX`: The 32-byte ECDSA private key.

## 🔐 Key Generation (OpenSSL)
To generate a valid key pair for the device:

```bash
# 1. Generate Private Key (keep this on the ESP32)
openssl ecparam -name prime256v1 -genkey -noout -out private.pem

# 2. Extract Public Key (Register this on the Backend)
openssl ec -in private.pem -pubout -out public.pem
```

*Note: You may need to convert the keys to Hexadecimal string format for the firmware.*

## ⚡ Flashing
1.  Connect the ESP32-C3 via USB.
2.  Open the folder in **VS Code** with **PlatformIO** installed.
3.  Click the **Upload** (Arrow) button.