# Frontend - Mobile App 📱

The mobile interface for the EDEAS system. It allows users to view real-time measurements, manage registered devices, and receive seismic alerts.

## 🛠 Tech Stack
* **Framework:** React Native
* **Platform:** Expo (Managed Workflow)
* **Navigation:** React Navigation (Native Stack + Bottom Tabs)
* **Maps:** React Native Maps (Currently disabled for dev stability)

## ⚙️ Configuration

1.  Create a `.env` file in the root of this folder:

    ```ini
    # REPLACE with your PC's Local IP Address (e.g., 192.168.1.50)
    # Do NOT use localhost (your phone cannot see localhost)
    EXPO_PUBLIC_API_URL=http://192.168.1.X:8000
    EXPO_PUBLIC_API_TIMEOUT=5000
    ```

## 🚀 Running the App

1.  Install dependencies:
    ```bash
    npm install
    ```
    *Note: If you encounter authentication errors, run `npm logout` first.*

2.  Start the Expo server:
    ```bash
    npx expo start -c
    ```
    *(The `-c` flag clears the cache, recommended for config changes)*.

3.  Scan the **QR Code** using the **Expo Go** app on your Android or iOS device.

## 🔑 Login Credentials (Dev Bypass)
For development purposes, you can bypass the standard authentication:
* **Email:** `admin@example.com`
* **Password:** `admin`

## 🧩 Project Structure
* `App.js`: Main entry point and Navigation configuration.
* `src/screens/`: Contains all UI views (Dashboard, Devices, Alerts, Login).
* `app.json`: Expo configuration.