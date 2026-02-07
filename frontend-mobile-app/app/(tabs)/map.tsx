import { Radio } from "lucide-react-native";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import MapView, { Callout, Marker, PROVIDER_DEFAULT } from "react-native-maps";
import { useQuakeStore } from "../../store/quakeStore";

export default function MapScreen() {
  const { sensors, fetchSensors } = useQuakeStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initData = async () => {
      await fetchSensors();
      setLoading(false);
    };
    initData();
  }, []);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#dc2626" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <MapView
        style={styles.map}
        provider={PROVIDER_DEFAULT}
        initialRegion={{
          latitude: 41.9028, // Default fallback (Rome, Italy)
          longitude: 12.4964,
          latitudeDelta: 5,
          longitudeDelta: 5,
        }}
      >
        {sensors.map((sensor) => (
          <Marker
            key={sensor.id}
            coordinate={{ latitude: sensor.lat, longitude: sensor.lon }}
            pinColor={sensor.status === "Active" ? "green" : "gray"}
          >
            <Callout tooltip={false}>
              <View style={styles.calloutContainer}>
                <Text style={styles.calloutTitle}>Sensor ID: {sensor.id}</Text>
                <View style={styles.statusRow}>
                  <Radio
                    size={14}
                    color={sensor.status === "Active" ? "#16a34a" : "#6b7280"}
                  />
                  <Text
                    style={[
                      styles.statusText,
                      {
                        color:
                          sensor.status === "Active" ? "#16a34a" : "#6b7280",
                      },
                    ]}
                  >
                    {sensor.status}
                  </Text>
                </View>
              </View>
            </Callout>
          </Marker>
        ))}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
  },
  map: {
    width: "100%",
    height: "100%",
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  calloutContainer: {
    padding: 8,
    width: 140,
    backgroundColor: "white",
    borderRadius: 6,
  },
  calloutTitle: {
    fontWeight: "700",
    fontSize: 14,
    marginBottom: 4,
    color: "#1f2937",
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: "500",
  },
});
