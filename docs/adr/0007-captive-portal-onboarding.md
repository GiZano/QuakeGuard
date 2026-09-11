# ADR-0007: Sensor Captive Portal for Zero-Touch Onboarding and APK Distribution

## Status
Accepted (v2.1.0)

## Context
Deploying an IoT network requires a seamless user experience for provisioning the physical devices. In a completely open-source project without central App Stores, asking users to manually compile the mobile app or manually extract cryptographic keys over serial ports creates excessive friction.
We needed a unified solution where turning on a freshly flashed ESP32-C3 node could instantly guide the user toward both joining the sensor to their local Wi-Fi and setting up their mobile device.

## Decision
We implemented a **Captive Portal Onboarding** strategy utilizing the ESP32's AP (Access Point) mode (`QuakeGuard-Setup`). 

When the user connects to this Wi-Fi network, a custom embedded HTML page is served with the following capabilities:
1. **Wi-Fi Provisioning:** The user can select their home SSID and enter the password (via `WiFiManager`).
2. **APK Distribution:** A prominent "Download QuakeGuard App" button directs the user to the GitHub Releases `latest` tag, allowing them to directly sideload the Android APK.
3. **Zero-Trust Device Enrollment:** The page generates and displays the sensor's unique **ECDSA Public Key** in clear-text. The user simply copies this key and pastes it into the mobile app to securely enroll the node in their personal network.

**Hardware Reset Fallback:** Because `WiFiManager` disables the Captive Portal once connected to a valid Wi-Fi network, we mapped the physical `BOOT` button (GPIO 0) on the ESP32 to trigger a credential wipe if held for 5 seconds. This forces the device back into AP mode, allowing users to recover their ECDSA public key or download the app again at any time in the future without degrading the sensor's Wi-Fi polling latency (which would happen if the AP was left permanently on in dual `WIFI_AP_STA` mode).

## Consequences
- **Positive:** **Zero-touch mobile distribution**. Users do not need to navigate GitHub or rely on Google Play to get the app; the sensor hardware itself serves as the distribution vector.
- **Positive:** Extreme UX simplification for ECDSA key exchange. Eliminates the need for serial monitors.
- **Positive:** Works purely offline initially, making it robust in diverse deployment environments.
- **Negative:** Embedded HTML strings consume flash memory (PROGMEM) on the ESP32.
- **Negative:** The user must know how to bypass Android's "Unknown Sources" warning when sideloading the APK.
