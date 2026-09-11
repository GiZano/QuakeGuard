import React, { useState } from "react";
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ScrollView, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Network, Trash2, BarChart2 } from "lucide-react-native";
import { useAppTheme } from "../../theme/useTheme";
import { MONO } from "../../theme";
import { useDeviceStore } from "../../store/useDeviceStore";

export default function DevicesScreen() {
  const { colors } = useAppTheme();
  const styles = createStyles(colors);
  
  const { devices, addDevice, removeDevice } = useDeviceStore();
  
  const [newLabel, setNewLabel] = useState("");
  const [newPublicKey, setNewPublicKey] = useState("");

  const handlePair = () => {
    if (!newLabel.trim() || !newPublicKey.trim()) {
      Alert.alert("Missing info", "Please provide both a label and a public key.");
      return;
    }
    
    // Simple validation (can be expanded)
    if (devices.some(d => d.publicKey === newPublicKey.trim())) {
      Alert.alert("Duplicate", "This device is already paired.");
      return;
    }

    addDevice(newPublicKey.trim(), newLabel.trim());
    setNewLabel("");
    setNewPublicKey("");
  };

  const handleUnpair = (publicKey: string, label: string) => {
    Alert.alert(
      "Unpair Device",
      `Are you sure you want to remove "${label}"?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Unpair",
          style: "destructive",
          onPress: () => removeDevice(publicKey),
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Network size={28} color={colors.alert} />
          <Text style={styles.headerTitle}>MY DEVICES</Text>
        </View>

        {/* Paired Sensors Section */}
        <Text style={styles.sectionTitle}>PAIRED SENSORS</Text>
        <View style={styles.card}>
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>SENSOR LABEL</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. Living Room Node"
              placeholderTextColor={colors.textMuted}
              value={newLabel}
              onChangeText={setNewLabel}
            />
          </View>
          
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>ECDSA PUBLIC KEY</Text>
            <TextInput
              style={styles.input}
              placeholder="Paste key from Captive Portal"
              placeholderTextColor={colors.textMuted}
              value={newPublicKey}
              onChangeText={setNewPublicKey}
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <TouchableOpacity style={styles.pairButton} onPress={handlePair}>
            <Text style={styles.pairButtonText}>PAIR DEVICE</Text>
          </TouchableOpacity>

          {devices.length > 0 && (
            <View style={styles.deviceList}>
              <Text style={styles.listTitle}>YOUR SENSORS</Text>
              {devices.map((device) => (
                <View key={device.publicKey} style={styles.deviceItem}>
                  <View style={styles.deviceInfo}>
                    <Text style={styles.deviceLabel}>{device.label}</Text>
                    <Text style={styles.deviceKey} numberOfLines={1} ellipsizeMode="middle">
                      {device.publicKey}
                    </Text>
                  </View>
                  <TouchableOpacity onPress={() => handleUnpair(device.publicKey, device.label)}>
                    <Trash2 size={20} color={colors.alert} />
                  </TouchableOpacity>
                </View>
              ))}
            </View>
          )}
        </View>

        {/* Sensor Data Section */}
        <Text style={[styles.sectionTitle, styles.sectionTitleSpaced]}>SENSOR DATA</Text>
        <View style={styles.card}>
          <View style={styles.placeholderContainer}>
            <BarChart2 size={48} color={colors.textMuted} />
            <Text style={styles.placeholderText}>Real-time data visualization coming soon</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (c: ReturnType<typeof useAppTheme>["colors"]) =>
  StyleSheet.create({
    safeArea: { flex: 1, backgroundColor: c.bg },
    container: { padding: 20, paddingBottom: 100 },
    header: { flexDirection: "row", alignItems: "center", marginBottom: 30, marginTop: 10, gap: 10 },
    headerTitle: { fontSize: 22, fontWeight: "bold", color: c.text, letterSpacing: 1.5, fontFamily: MONO },
    sectionTitle: {
      fontSize: 11,
      color: c.textMuted,
      fontWeight: "700",
      letterSpacing: 1.5,
      fontFamily: MONO,
      marginBottom: 8,
      marginTop: 4,
    },
    sectionTitleSpaced: { marginTop: 24 },
    card: {
      backgroundColor: c.surface,
      borderColor: c.border,
      borderWidth: 1,
      borderRadius: 16,
      padding: 16,
    },
    inputGroup: {
      marginBottom: 16,
    },
    inputLabel: {
      fontSize: 11,
      fontFamily: MONO,
      color: c.textSecondary,
      marginBottom: 6,
      letterSpacing: 1,
    },
    input: {
      borderWidth: 1,
      borderColor: c.borderStrong,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 10,
      color: c.text,
      fontFamily: MONO,
      backgroundColor: c.bg,
    },
    pairButton: {
      backgroundColor: c.live,
      borderRadius: 8,
      paddingVertical: 12,
      alignItems: "center",
      marginTop: 8,
    },
    pairButtonText: {
      color: c.bg,
      fontSize: 14,
      fontWeight: "700",
      fontFamily: MONO,
      letterSpacing: 1,
    },
    deviceList: {
      marginTop: 24,
      borderTopWidth: 1,
      borderTopColor: c.border,
      paddingTop: 16,
    },
    listTitle: {
      fontSize: 11,
      fontFamily: MONO,
      color: c.textSecondary,
      marginBottom: 12,
      letterSpacing: 1,
    },
    deviceItem: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      backgroundColor: c.bg,
      padding: 12,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: c.borderStrong,
      marginBottom: 8,
    },
    deviceInfo: {
      flex: 1,
      marginRight: 12,
    },
    deviceLabel: {
      fontSize: 15,
      fontWeight: "600",
      color: c.text,
      marginBottom: 4,
    },
    deviceKey: {
      fontSize: 11,
      fontFamily: MONO,
      color: c.textMuted,
    },
    placeholderContainer: {
      alignItems: "center",
      justifyContent: "center",
      paddingVertical: 32,
      gap: 16,
    },
    placeholderText: {
      color: c.textMuted,
      fontFamily: MONO,
      fontSize: 12,
      textAlign: "center",
    },
  });
