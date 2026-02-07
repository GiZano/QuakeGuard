import { ShieldAlert, ShieldCheck } from "lucide-react-native";
import React, { useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { useQuakeStore } from "../../store/quakeStore";

export default function MonitorScreen() {
  const { systemStatus, startMonitoring, stopMonitoring } = useQuakeStore();

  // Shared value for the pulse animation
  const pulse = useSharedValue(1);

  // Lifecycle management for polling
  useEffect(() => {
    startMonitoring();
    return () => {
      stopMonitoring();
    };
  }, []);

  // Animation logic triggered by status change
  useEffect(() => {
    if (systemStatus === "ALERT") {
      pulse.value = withRepeat(
        withSequence(
          withTiming(1.2, { duration: 300, easing: Easing.inOut(Easing.ease) }),
          withTiming(1, { duration: 300, easing: Easing.inOut(Easing.ease) }),
        ),
        -1, // Infinite loop
        true, // Reverse
      );
    } else {
      pulse.value = withTiming(1, { duration: 300 }); // Reset to default scale
    }
  }, [systemStatus]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulse.value }],
    opacity: systemStatus === "ALERT" ? pulse.value : 1, // Slight opacity effect during pulse
  }));

  const isSecure = systemStatus === "SECURE";

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: isSecure ? "#f0fdf4" : "#fef2f2" },
      ]}
    >
      <Animated.View style={[styles.iconContainer, animatedStyle]}>
        {isSecure ? (
          <ShieldCheck size={120} color="#16a34a" />
        ) : (
          <ShieldAlert size={120} color="#dc2626" />
        )}
      </Animated.View>

      <Text
        style={[styles.statusText, { color: isSecure ? "#166534" : "#991b1b" }]}
      >
        {isSecure ? "SYSTEM SECURE" : "⚠️ SEISMIC ALERT ⚠️"}
      </Text>

      <Text style={styles.subText}>
        {isSecure
          ? "No recent seismic activity detected."
          : "Critical seismic activity detected in Zone 1."}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  iconContainer: {
    marginBottom: 40,
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.1,
    shadowRadius: 5.46,
    elevation: 9,
  },
  statusText: {
    fontSize: 28,
    fontWeight: "800",
    marginBottom: 12,
    textAlign: "center",
    letterSpacing: 0.5,
  },
  subText: {
    fontSize: 16,
    color: "#4b5563",
    textAlign: "center",
    maxWidth: "80%",
    lineHeight: 24,
  },
});
