# 🌋 QuakeGuard - Electro-Domestic Alarm System

**Version:** 3.0.0 (Stable)  
**Status:** Active Development  
**License:** MIT  

---

## 📖 Overview
QuakeGuard is a **Full-Stack IoT** architecture designed for the real-time detection, analysis, and reporting of seismic events. 
The system utilizes intelligent edge sensors (ESP32) that analyze vibrations locally and transmit encrypted data (ECDSA) to an asynchronous hybrid Cloud, capable of handling the massive traffic spikes (**Thundering Herd** effect) typical during earthquake events.



---

## 🏗 System Architecture

The project is modular and follows **Microservices** and **Event-Driven Design** principles:

### 1. 📡 IoT Edge (Data Harvester)
* **Hardware:** ESP32-C3 SuperMini + ADXL345 Accelerometer.
* **Logic:** 100Hz sampling, Digital High-Pass Filters (HPF), and STA/LTA (Short Term/Long Term Average) algorithm.
* **Security:** Hardware-level digital signing of payloads using **ECDSA (NIST256p)**.
* **Resilience:** Temporal timestamp reconstruction to mitigate network latency issues.

### 2. ☁️ Backend (Data Elaborator)
* **Core:** FastAPI (Python).
* **Pattern:** Producer-Consumer with **Redis** as a Message Broker.
* **Persistence:** PostgreSQL + PostGIS for geospatial data management.
* **Worker:** Background processes for queue consumption and alarm aggregation.
* **Performance:** Asynchronous management capable of handling >500 Req/s on standard hardware.

### 3. 📱 Frontend (Mobile Monitor)
* **Framework:** React Native (Expo).
* **Features:** Dashboard with real-time visual/haptic alarms (Adaptive Polling) and an interactive sensor map.

---

## 🚀 Quick Start (Local Deployment)

### Prerequisites
* Docker & Docker Compose
* PlatformIO (VS Code Extension)
* Node.js & Expo Go

### 1. Launch the Backend
```bash
cd "Backend - Data Elaborator"
docker-compose up --build -d
# Backend will be live at http://localhost:8000
```

### 2. Configure and Flash the IoT Device
1.  Modify ```IoT - Data Harvester/esp32_config.env``` with your local IP and WiFi credentials.
2.  Upload the firmware to the ESP32.
3.  **IMPORTANT:** On the first boot, copy the ```PUBLIC KEY``` from the serial monitor and register it via Swagger (```http://localhost:8000/docs```).

### 3. Launch the Mobile App
```bash
cd "Frontend - Mobile App"
npm install
npx expo start
# Scan the QR code with your smartphone (must be on the same WiFi)
```

---

## 🔐 Security Architecture
Each packet sent by the sensors contains:  
```{ value: 250, timestamp: 17000000, signature: "a1b2..." }```

The backend cryptographically verifies the signature (**SHA256 + ECDSA**) before accepting the data, preventing **Man-in-the-Middle** and **Spoofing** attacks.
