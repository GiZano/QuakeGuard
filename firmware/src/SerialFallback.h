#pragma once

#include <array>
#include <cstdio>
#include <string>

#ifndef SERIAL_FALLBACK_MARKER
#define SERIAL_FALLBACK_MARKER "[QG:FB]"
#endif

/**
 * SerialFallback — pure-C++ USB serial fallback core.
 *
 * When the MQTT data plane is unreachable, the node re-certifies each
 * seismic event and emits it over the USB CDC port so a co-located host can
 * read it and forward it to the ingestion pipeline. Like DetectionCore.h, this
 * translation unit is fully decoupled from the ESP32 hardware (no Arduino,
 * FreeRTOS, I2C or WiFi): it is the single source of truth shared by the
 * firmware (networkTask) and the host-side SIL validation (test_serial_fallback).
 *
 * The frame format mirrors the MQTT payload exactly:
 *   [QG:FB]{"value":<int>,"sensor_id":<int>,"device_timestamp":<unix>,"signature_hex":"<hex>"}
 *
 * The marker lets the host bridge filter out regular boot/log noise from
 * machine-readable telemetry frames.
 */

// A retained seismic event, kept when no delivery path is available.
struct SerialEvent {
    int value;
    long timestamp; // original event time (unix seconds)
};

// FIFO retention ring with bounded capacity (overwrites oldest when full).
template <size_t S>
class RetentionRing {
public:
    void push(const SerialEvent& evt) {
        buffer_[head_] = evt;
        head_ = (head_ + 1) % S;
        if (count_ < S) count_++;
    }

    bool empty() const { return count_ == 0; }
    size_t size() const { return count_; }

    // Pop the oldest retained event (FIFO). Returns false when empty.
    bool pop(SerialEvent& out) {
        if (count_ == 0) return false;
        size_t tail = (head_ + S - count_) % S;
        out = buffer_[tail];
        count_--;
        return true;
    }

private:
    std::array<SerialEvent, S> buffer_{};
    size_t head_ = 0; // next write position
    size_t count_ = 0;
};

// Routing decision: which delivery path an event should take.
enum class DeliveryPath {
    MQTT,        // broker reachable -> publish (unchanged data plane)
    SERIAL_CDC,  // broker unreachable but USB host present and time is valid
    RETAIN       // no path available -> keep the event in the retention ring
};

// Pure routing decision shared by firmware and host validation.
inline DeliveryPath decidePath(bool mqttReachable, bool usbHostPresent, bool timeValid) { // NOSONAR(cpp:S5811) - using enum requires C++20, ESP32 toolchain is C++11
    if (mqttReachable) return DeliveryPath::MQTT;
    if (usbHostPresent && timeValid) return DeliveryPath::SERIAL_CDC;
    return DeliveryPath::RETAIN;
}

// Build a [QG:FB] serial frame carrying the exact MQTT data-plane payload.
inline std::string buildSerialFrame(const std::string& marker, // NOSONAR(cpp:S995) - string_view requires C++17, ESP32 toolchain is C++11
                                    int value,
                                    int sensorId,
                                    long deviceTimestamp,
                                    const std::string& signatureHex,
                                    long long deviceTimestampMs = 0,
                                    int freeHeap = 0,
                                    int rssi = 0,
                                    int gnssSatellites = 0) { // NOSONAR(cpp:S995)
    std::string frame;
    frame.reserve(marker.size() + 128 + signatureHex.size());

    frame += marker;
    frame += R"({"value":)";
    frame += std::to_string(value);
    frame += R"(,"sensor_id":)";
    frame += std::to_string(sensorId);
    frame += R"(,"device_timestamp":)";
    frame += std::to_string(deviceTimestamp);
    if (deviceTimestampMs > 0) {
        frame += R"(,"device_timestamp_ms":)";
        frame += std::to_string(deviceTimestampMs);
    }
    if (freeHeap > 0) {
        frame += R"(,"free_heap":)";
        frame += std::to_string(freeHeap);
    }
    if (rssi != 0) {
        frame += R"(,"rssi":)";
        frame += std::to_string(rssi);
    }
    if (gnssSatellites > 0) {
        frame += R"(,"gnss_satellites":)";
        frame += std::to_string(gnssSatellites);
    }
    frame += R"(,"signature_hex":")";
    frame += signatureHex;
    frame += R"("})";
    return frame;
}
