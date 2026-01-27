# Electro-Domestic Earthquake Alarm System (EDEAS) 🌋

**Project Status:** Active Development (Alpha)

## 📖 Overview
EDEAS is a full-stack IoT solution designed to detect, analyze, and visualize seismic activity in domestic environments. The system utilizes low-cost hardware (ESP32) to capture vibration data, securely transmits it to a central server via ECDSA-signed payloads, and visualizes alerts and status via a mobile application.

## 🏗 Project Architecture

The repository is organized into three distinct modules:

* **📂 Backend - Data Elaborator:** The brain of the system. A FastAPI server with a PostgreSQL/PostGIS database. It handles device registration, cryptographic verification, data ingestion, and seismic alert logic.
* **📂 Frontend - Mobile App:** The user interface. A React Native (Expo) application for monitoring sensor status, viewing real-time alerts, and managing devices.
* **📂 IoT - Data Harvester:** The edge layer. Firmware for ESP32-C3 SuperMini connected to ADXL345 accelerometers. It handles sampling, signing, and transmission.

## 🚀 Quick Start Guide

To run the entire ecosystem locally, follow this order of operations:

1.  **Start the Backend:**
    Navigate to `Backend - Data Elaborator` and launch the Docker containers. The database must be running for the other components to work.
2.  **Flash the Firmware:**
    Configure and flash the ESP32 devices in `IoT - Data Harvester`. Ensure they have the correct Public/Private keys.
3.  **Launch the Mobile App:**
    Navigate to `Frontend - Mobile App` and start the Expo server to connect via your smartphone.

## 🔐 Security Architecture
The system implements **ECDSA (Elliptic Curve Digital Signature Algorithm)** on curve **NIST256p**.
* **Device:** Holds the Private Key. Signs payload `value:timestamp`.
* **Server:** Holds the Public Key. Verifies the signature before accepting data.

---
*For detailed instructions, refer to the README.md files within each subdirectory.*