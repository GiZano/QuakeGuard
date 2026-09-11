# ADR-0008: In-App OTA Updates via GitHub Releases

## Status
Accepted (v2.1.0)

## Context
QuakeGuard's React Native mobile app is distributed as a sideloaded APK (not via Play Store/App Store during the development phase). Users need a reliable mechanism to receive updates without manually downloading and installing new APK files. The update mechanism must work for sideloaded apps and not depend on app store infrastructure.

## Decision
Implement a custom **Over-the-Air (OTA) updater** inside the React Native app that polls GitHub Releases for new versions.

1. **Version Polling Hook (`useUpdateChecker`):** A custom React hook runs on app launch, comparing the app's bundled version against the latest GitHub Release tag via the GitHub API (`GET /repos/GiZano/QuakeGuard/releases/latest`).
2. **Native Sideload Prompt:** When a newer version is detected, the app displays a native `Alert` prompt with the release notes. On confirmation, it triggers the browser to download the APK asset from the release, leveraging Android's built-in APK installation flow.
3. **Captive Portal Distribution:** The ESP32 Captive Portal (`WiFiManager`) serves a direct download link to the latest APK, enabling first-time installation for users pairing a new sensor.
4. **No Expo EAS Dependency:** The update mechanism is intentionally decoupled from Expo's EAS Update service to maintain full self-hosting capability and avoid vendor lock-in.

## Consequences
- **Positive:** Users receive update prompts automatically on app launch without checking GitHub manually.
- **Positive:** The Captive Portal provides a zero-touch installation path for new users.
- **Positive:** Full control over the update distribution pipeline with no third-party dependencies.
- **Negative:** Android-only for now; iOS sideloading requires additional steps (TestFlight or enterprise distribution).
- **Negative:** The GitHub API has rate limits (60 req/hour unauthenticated), but the app polls only once per launch, making this a non-issue.
