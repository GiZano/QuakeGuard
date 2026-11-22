#pragma once

#include <cmath>
#include "RingBuffer.h"

/**
 * SeismicDetector — pure-C++ STA/LTA detection core.
 *
 * Fully decoupled from the ESP32 hardware: no Arduino, FreeRTOS, I2C or WiFi
 * calls in this translation unit. This is the single source of truth used both
 * by the firmware (sensorTask) and by the host SIL validation (detect_cli),
 * guaranteeing numerical equivalence.
 *
 * The detector is clock-injected: callers pass an absolute "now" in
 * milliseconds. The firmware passes millis(); the host passes sample_index * 10
 * at 100 Hz. This keeps the detection decision identical on both targets.
 */
class SeismicDetector {
public:
    static constexpr float DEFAULT_HPF_ALPHA = 0.9f;
    static constexpr float DEFAULT_TRIGGER_RATIO = 2.4f;
    static constexpr float DEFAULT_NOISE_FLOOR = 0.04f;
    static constexpr float DEFAULT_LTA_FLOOR = 0.01f;
    static constexpr size_t STA_WINDOW = 100;   // 1 s @ 100 Hz
    static constexpr size_t LTA_WINDOW = 1000;  // 10 s @ 100 Hz
    static constexpr unsigned long COOLDOWN_MS = 5000;
    static constexpr float INITIAL_RAW = 9.81f; // gravity baseline

    explicit SeismicDetector(float hpfAlpha = DEFAULT_HPF_ALPHA,
                             float triggerRatio = DEFAULT_TRIGGER_RATIO,
                             float noiseFloor = DEFAULT_NOISE_FLOOR);

    /**
     * Euclidean norm of a 3-axis acceleration sample (the single shared
     * definition of "magnitude" used by firmware and host).
     */
    static float norm3(float x, float y, float z) {
        return std::sqrt(x * x + y * y + z * z);
    }

    /**
     * Feed one raw acceleration magnitude (norm of the 3 axes).
     * Returns true when a seismic event is detected.
     */
    bool push(float rawMag, unsigned long nowMs);

    // Ratio of the last evaluated sample (STA/LTA).
    float lastRatio() const { return ratio_; }
    // STA of the last evaluated sample.
    float lastSTA() const { return sta_; }

private:
    float hpfAlpha_;
    float triggerRatio_;
    float noiseFloor_;

    float filtered_ = 0.0f;  // HPF state
    float prevRaw_ = INITIAL_RAW;

    RingBuffer<STA_WINDOW> staBuf_;
    RingBuffer<LTA_WINDOW> ltaBuf_;

    bool inAlarm_ = false;
    unsigned long alarmStartMs_ = 0;

    float sta_ = 0.0f;
    float ratio_ = 0.0f;
};

// ---------------------------------------------------------------------------
// Implementation (header-only)
// ---------------------------------------------------------------------------

inline SeismicDetector::SeismicDetector(float hpfAlpha, float triggerRatio, float noiseFloor)
    : hpfAlpha_(hpfAlpha), triggerRatio_(triggerRatio), noiseFloor_(noiseFloor) {}

inline bool SeismicDetector::push(float rawMag, unsigned long nowMs) {
    // High-pass filter to remove gravity. NOTE: uses std::abs; on-firmware the
    // same expression is used so results are bit-identical on host vs ESP32.
    filtered_ = hpfAlpha_ * (filtered_ + rawMag - prevRaw_);
    prevRaw_ = rawMag;
    float abs_signal = filtered_ < 0.0f ? -filtered_ : filtered_;

    // Noise gate.
    if (abs_signal < noiseFloor_) abs_signal = 0.0f;

    staBuf_.push(abs_signal);
    ltaBuf_.push(abs_signal);

    // Do not trigger until the full LTA window is populated.
    if (!ltaBuf_.isFull()) return false;

    sta_ = staBuf_.average();
    float lta = ltaBuf_.average();
    if (lta < DEFAULT_LTA_FLOOR) lta = DEFAULT_LTA_FLOOR; // division-by-zero guard

    ratio_ = sta_ / lta;

    bool triggered = false;
    if (ratio_ >= triggerRatio_ && sta_ > noiseFloor_ && !inAlarm_) {
        inAlarm_ = true;
        alarmStartMs_ = nowMs;
        triggered = true;
    }

    if (inAlarm_ && (nowMs - alarmStartMs_ > COOLDOWN_MS)) {
        inAlarm_ = false;
    }

    return triggered;
}