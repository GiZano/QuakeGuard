/**
 * Project: QuakeGuard - Professional Seismic Node
 * Optional GNSS sub-system (v2.0.0).
 *
 * Compiled ONLY when `GNSS_ENABLED=1` is present in esp32_config.env. The
 * default build remains hermetic (no TinyGPSPlus dependency is pulled).
 *
 * Responsibilities at this stage (v2.0.0):
 *   - Parse NMEA from a u-blox / NEO-6M / NEO-M8N module on UART.
 *   - Persist the last reliable fix in NVS so provisioning can report real
 *     coordinates even before the first fix after a cold boot.
 *   - Expose the most recent fix (live GNSS, or last-known-from-NVS).
 *
 * NTP + PPS timestamp discipline is v2.0.0 scope (see ROADMAP): this module
 * only guarantees the coordinates pipeline is ready for the GNSS upgrade.
 */

#ifndef QUAKEGUARD_GNSS_MODULE_H
#define QUAKEGUARD_GNSS_MODULE_H

#include <Arduino.h>

#ifdef GNSS_ENABLED

#include <HardwareSerial.h>
#include <Preferences.h>
#include <TinyGPSPlus.h>

#ifndef GPS_SERIAL_RX_PIN
  #define GPS_SERIAL_RX_PIN 5
#endif
#ifndef GPS_SERIAL_TX_PIN
  #define GPS_SERIAL_TX_PIN 4
#endif
#ifndef GPS_SERIAL_BAUD
  #define GPS_SERIAL_BAUD 9600
#endif
#ifndef GPS_PPS_PIN
  #define GPS_PPS_PIN 2
#endif

namespace quakeguard_gnss {
constexpr const char* GNSS_NVS_NAMESPACE = "quake-gnss";
constexpr const char* GNSS_NVS_LAT = "lat";
constexpr const char* GNSS_NVS_LON = "lon";
constexpr const char* GNSS_NVS_VALID = "valid";

// Save the last-known fix at most once per this interval (NVS wear levelling).
constexpr unsigned long GNSS_SAVE_INTERVAL_MS = 60000UL;
// A live fix older than this is treated as stale (fall back to last-known).
constexpr unsigned long GNSS_FIX_MAX_AGE_MS = 10000UL;
}

struct GnssFix {
  float latitude;
  float longitude;
  bool valid;
  unsigned long age_ms;      // elapsed since this fix was obtained
  bool from_storage;         // true when served from NVS last-known
};

class GnssModule {
public:
  void begin();
  void loop();
  bool getFix(GnssFix& out);
  // PPS (v2.0.0) — returns millis() of last PPS pulse, 0 if never seen
  unsigned long getLastPpsMs() const { return lastPpsMs_; }
  bool hasPpsFix() const { return lastPpsMs_ != 0 && (millis() - lastPpsMs_) < 2000; }
  uint32_t getSatellites() { return gps_.satellites.isValid() ? gps_.satellites.value() : 0; }

private:
  void saveLastKnownFix();
  void loadLastKnownFix();
  static void IRAM_ATTR onPpsIsr();

  HardwareSerial serial_{1};
  TinyGPSPlus gps_;
  Preferences prefs_;

  bool last_known_valid_ = false;
  float last_known_lat_ = 0.0f;
  float last_known_lon_ = 0.0f;
  unsigned long last_save_ms_ = 0;
  static volatile unsigned long lastPpsMs_;
};

GnssModule& gnss();

#endif // GNSS_ENABLED
#endif // QUAKEGUARD_GNSS_MODULE_H