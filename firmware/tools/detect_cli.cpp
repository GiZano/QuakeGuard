// QuakeGuard host SIL CLI — drives the SAME SeismicDetector used on the ESP32.
//
// Input (stdin): one CSV line per sample:  t,ax,ay,az
//   t   : timestamp in seconds (float, 100 Hz => step 0.01)
//   ax, ay, az : raw acceleration in m/s^2 (same units as the firmware's
//                Adafruit sensors_event_t; gravity baseline ~9.8 m/s^2 on Z)
// Lines starting with '#' are ignored (header support).
//
// Output (stdout): one line per detected event:  t,ratio
//
// Parameters (argv, all optional):
//   1: TRIGGER_RATIO  (default 2.4, matches SeismicDetector::DEFAULT_TRIGGER_RATIO)
//   2: NOISE_FLOOR    (default 0.04)
//   3: HPF_ALPHA      (default 0.9)
//
// Build (host):  g++ -std=c++11 -I src tools/detect_cli.cpp -o detect_cli

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <iostream>
#include <string>
#include "DetectionCore.h"

int main(int argc, char** argv) {
    float triggerRatio = SeismicDetector::DEFAULT_TRIGGER_RATIO;
    float noiseFloor = SeismicDetector::DEFAULT_NOISE_FLOOR;
    float hpfAlpha = SeismicDetector::DEFAULT_HPF_ALPHA;

    if (argc > 1) triggerRatio = static_cast<float>(atof(argv[1]));
    if (argc > 2) noiseFloor = static_cast<float>(atof(argv[2]));
    if (argc > 3) hpfAlpha = static_cast<float>(atof(argv[3]));

    SeismicDetector det(hpfAlpha, triggerRatio, noiseFloor);

    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty() || line[0] == '#') continue;

        double t = 0.0;
        double ax = 0.0;
        double ay = 0.0;
        double az = 0.0;
        if (std::sscanf(line.c_str(), "%lf,%lf,%lf,%lf", &t, &ax, &ay, &az) != 4) continue;

        auto raw = SeismicDetector::norm3(static_cast<float>(ax),
                                          static_cast<float>(ay),
                                          static_cast<float>(az));

        // 100 Hz => sample clock = t * 1000 ms (matches firmware millis()).
        auto nowMs = static_cast<unsigned long>(t * 1000.0);

        if (det.push(raw, nowMs)) {
            printf("%.3f,%.6f\n", t, det.lastRatio()); // NOSONAR(cpp:S6494)
            fflush(stdout);
        }
    }
    return 0;
}