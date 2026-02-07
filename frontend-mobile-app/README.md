# QuakeGuard - Mobile Application

**QuakeGuard Mobile** is a React Native application built with Expo (SDK 50+), designed to provide real-time monitoring of seismic activity. It interfaces with a custom Python backend and IoT sensor network to visualize system status and sensor locations.

## 🛠 Technology Stack

- **Framework:** React Native (Expo Router)
- **Language:** TypeScript
- **State Management:** Zustand
- **Maps:** React Native Maps
- **UI/Icons:** Lucide React Native
- **Animations:** React Native Reanimated

## 🚀 Features

### 1. 🛡️ Monitor Dashboard (Home)

- **Real-time Polling:** Automatically queries the backend (`GET /zones/1/alerts`) every 2 seconds.
- **Visual Status:** Displays a "System Secure" (Green) or "Seismic Alert" (Red) status based on recent data.
- **Haptic Feedback:** Triggers device vibration when the system state transitions from Secure to Alert.
- **Animations:** Uses `react-native-reanimated` for a pulsing shield effect during active alerts.

### 2. 🗺️ Sensor Map (WIP)

- **Data Visualization:** Fetches sensor coordinates (`GET /misurators/`) and displays them on a map interface.
- **Status Indicators:** Markers change color based on the active/inactive status of the sensor.

## ⚠️ Known Issues

- **Map Marker Crash:** navigating to the Map tab currently triggers the error: `Error while updating property 'coordinate' of a view managed by AIRMapMarker`.
  - _Status:_ Under Investigation.
  - _Suspected Cause:_ Data type mismatch (string vs number) in the coordinate payload from the backend.

## ⚙️ Installation & Setup

### 1. Prerequisites

Ensure you have the following installed:

- Node.js (LTS version recommended)
- Expo CLI
- The QuakeGuard Backend running locally.

### 2. Install Dependencies

Navigate to the project root and install the required packages:

```bash
npm install
# or
npx expo install
```

### 3. Configuration (Critical Step)

Before running the application, you must configure the API endpoint to match your local network environment. The application cannot access `localhost` if running on a physical device or Android Emulator.

Open `constants/config.ts` and update the IP address:

```typescript
// constants/config.ts
export const API_BASE_URL = "http://YOUR_LOCAL_IP:8000";
// Example: 'http://192.168.1.50:8000'
```

### 4. Running the Application

Start the development server:

```bash
npx expo start -c
```

- Press **"a"** to run on Android Emulator.
- Press **"i"** to run on iOS Simulator (macOS only).
- Scan the QR code with the **Expo Go** app to run on a physical device (ensure the device is on the same Wi-Fi network).

## 🐛 Troubleshooting

**Network Errors / Backend Unreachable:**
If the app fails to connect to the backend:

1.  Ensure the backend is running and accessible.
2.  Verify that your firewall allows connections on port 8000.
3.  **WSL Users:** If running the backend on WSL2, the network bridge might fail. Try running Expo with the tunnel option:

```bash
npx expo start --tunnel
```
