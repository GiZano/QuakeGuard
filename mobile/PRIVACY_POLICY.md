# QuakeGuard — Privacy Policy

**Last updated:** September 3, 2026
**Effective for:** QuakeGuard Mobile App (iOS / Android)

## Overview

QuakeGuard is an open-source earthquake early warning system. This privacy policy explains how the QuakeGuard mobile application collects, uses, and protects your information.

## Data We Collect

### 1. Device Location (Optional)
- **What:** Approximate GPS coordinates
- **Why:** To determine your seismic zone and calculate earthquake wave arrival time (ETA)
- **When:** Only when you explicitly enable "Detect my zone via GPS" in Settings
- **Storage:** Transmitted to the QuakeGuard backend for zone assignment; not stored persistently on the server beyond the session

### 2. Push Notification Token
- **What:** Device push notification token (Expo Push Token)
- **Why:** To deliver earthquake alerts even when the app is in the background
- **When:** Only when you enable notifications in Settings
- **Storage:** Used by the push notification service (Expo) to route alerts; not shared with third parties

### 3. App Preferences
- **What:** User settings (notification preferences, offline mode toggle, display preferences)
- **Why:** To remember your configuration between app sessions
- **Storage:** Stored locally on your device only (via Zustand persistence); never transmitted to any server

## Data We Do NOT Collect

- ❌ Personal identification (name, email, phone number)
- ❌ Contacts, photos, or files
- ❌ Browsing history or usage analytics
- ❌ Advertising identifiers
- ❌ Health or biometric data

## Data Transmission

All communication between the app and the QuakeGuard backend uses:
- **WebSocket (WSS)** for real-time alerts — authenticated via `MOBILE_WS_TOKEN`
- **HTTPS** for API calls — authenticated via `IOT_API_KEY`

No telemetry data is sent to third-party analytics services.

## Third-Party Services

| Service | Purpose | Data Shared |
|---------|---------|-------------|
| Expo | Push notifications delivery | Device push token |
| React Native Maps | Sensor network visualization | None (map tiles only) |

## Data Retention

- **Location data:** Not retained beyond the active session
- **Alert history:** Stored in-memory only (last 10 alerts); cleared on app restart
- **Preferences:** Stored locally on-device until the user clears app data

## Open Source Transparency

QuakeGuard is fully open source. You can audit exactly what data the app collects by reviewing the source code:
- **Repository:** [github.com/GiZano/QuakeGuard](https://github.com/GiZano/QuakeGuard)
- **Mobile source:** [`mobile/`](https://github.com/GiZano/QuakeGuard/tree/main/mobile)
- **License:** AGPL-3.0

## Children's Privacy

QuakeGuard does not knowingly collect data from children under 13. The app is a safety tool and does not contain age-restricted content.

## Your Rights

You can:
- **Disable location access** at any time via your device's system settings
- **Disable notifications** via the app's Settings screen or system settings
- **Delete all local data** by uninstalling the app

## Changes to This Policy

We may update this privacy policy to reflect changes in the app. Updates will be posted in this file in the repository and noted in the CHANGELOG.

## Contact

For privacy-related questions or concerns:
- **Email:** gizano.dev@gmail.com
- **Repository:** [github.com/GiZano/QuakeGuard](https://github.com/GiZano/QuakeGuard)
