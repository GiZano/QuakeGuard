import React, { useState, useRef, useEffect } from "react";
import { View, Text, StyleSheet, Switch, Alert, TouchableOpacity, ActivityIndicator, ScrollView, Linking } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams } from "expo-router";
import {
  Settings as SettingsIcon,
  Bell,
  WifiOff,
  Trash2,
  Microscope,
  RadioTower,
  MapPin,
  Crosshair,
  Globe,
  Github,
  ExternalLink,
} from "lucide-react-native";
import * as Location from "expo-location";
import { usePreferencesStore } from "../../store/usePreferencesStore";
import { useAlertStore } from "../../store/useAlertStore";
import { useThemeStore } from "../../store/useThemeStore";
import { useAppTheme } from "../../theme/useTheme";
import { useZones } from "../../api/hooks/useDashboard";
import { apiClient } from "../../api/client";
import { MONO } from "../../theme";

interface Zone {
  id: number;
  city: string;
}

export default function SettingsScreen() {
  const {
    isOfflineMode,
    notificationsEnabled,
    homeZoneId,
    setOfflineMode,
    toggleNotifications,
    setHomeZoneId,
  } = usePreferencesStore();
  const { clearAlerts, alerts } = useAlertStore();
  const { colors, mode } = useAppTheme();
  const { toggleTheme } = useThemeStore();
  const { data: zones } = useZones();
  const [detecting, setDetecting] = useState(false);
  const styles = createStyles(colors);
  
  const params = useLocalSearchParams();
  const scrollRef = useRef<ScrollView>(null);
  const [zoneSectionY, setZoneSectionY] = useState(0);

  useEffect(() => {
    if (params.scroll === "zone" && zoneSectionY > 0) {
      setTimeout(() => {
        scrollRef.current?.scrollTo({ y: zoneSectionY, animated: true });
      }, 100);
    }
  }, [params.scroll, zoneSectionY]);

  const handleClearHistory = () => {
    if (alerts.length === 0) return;

    Alert.alert(
      "Clear History",
      "Are you sure you want to delete all recent alerts?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Clear",
          style: "destructive",
          onPress: () => {
            clearAlerts();
            console.log("[Settings] Alert history cleared.");
          },
        },
      ]
    );
  };

  const myZoneCity =
    homeZoneId == null
      ? "ALL REGIONS (ring for every alert)"
      : (zones as Zone[] | undefined)?.find((z) => z.id === homeZoneId)?.city;

  const handleDetectZone = async () => {
    if (isOfflineMode) {
      Alert.alert("Offline", "Connect to the network to detect your zone.");
      return;
    }

    setDetecting(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== Location.PermissionStatus.GRANTED) {
        Alert.alert("Permission denied", "Location access is required to detect your zone. Pick it manually below.");
        return;
      }

      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      const { data } = await apiClient.get<Zone>("/zones/locate", {
        params: { latitude: position.coords.latitude, longitude: position.coords.longitude },
      });

      setHomeZoneId(data.id);
      Alert.alert("Zone updated", `Your area resolved to "${data.city}". Alerts will now ring only for this region.`);
    } catch (err: any) {
      if (err?.response?.status === 404) {
        Alert.alert(
          "Outside monitored area",
          "Your position is not covered by a monitored polygon. Pick a zone manually below."
        );
      } else {
        Alert.alert("Detection failed", "Could not resolve your zone. Pick one manually below.");
      }
    } finally {
      setDetecting(false);
    }
  };

  const selectZone = (zoneId: number | null) => {
    setHomeZoneId(zoneId);
    const city =
      zoneId == null
        ? "ALL REGIONS"
        : (zones as Zone[] | undefined)?.find((z) => z.id === zoneId)?.city ?? `Zone #${zoneId}`;
    console.log(`[Settings] Home zone set: ${city}`);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView ref={scrollRef} contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <SettingsIcon size={28} color={colors.alert} />
          <Text style={styles.headerTitle}>SYSTEM CONFIG</Text>
        </View>

        {/* Appearance */}
        <Text style={styles.sectionTitle}>APPEARANCE</Text>
        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingLabelContainer}>
              {mode === "dark" ? <RadioTower size={22} color={colors.live} /> : <Microscope size={22} color={colors.info} />}
              <View>
                <Text style={styles.settingLabel}>
                  {mode === "dark" ? "MIC MODE (Military)" : "RESEARCH MODE"}
                </Text>
                <Text style={styles.settingHint}>
                  {mode === "dark" ? "Dark command console" : "Light scientific study"}
                </Text>
              </View>
            </View>
            <Switch
              value={mode === "light"}
              onValueChange={toggleTheme}
              trackColor={{ false: colors.borderStrong, true: colors.info }}
              thumbColor={mode === "light" ? colors.info : colors.textMuted}
            />
          </View>
        </View>

        {/* Alerts */}
        <Text style={[styles.sectionTitle, styles.sectionTitleSpaced]}>GLOBAL</Text>
        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingLabelContainer}>
              <Bell size={22} color={colors.textSecondary} />
              <Text style={styles.settingLabel}>Enable Notifications</Text>
            </View>
            <Switch
              value={notificationsEnabled}
              onValueChange={toggleNotifications}
              trackColor={{ false: colors.borderStrong, true: colors.alert }}
              thumbColor={notificationsEnabled ? "#f87171" : colors.textMuted}
            />
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingLabelContainer}>
              <WifiOff size={22} color={colors.textSecondary} />
              <Text style={styles.settingLabel}>Force Offline Mode</Text>
            </View>
            <Switch
              value={isOfflineMode}
              onValueChange={setOfflineMode}
              trackColor={{ false: colors.borderStrong, true: colors.alert }}
              thumbColor={isOfflineMode ? "#f87171" : colors.textMuted}
            />
          </View>

          <TouchableOpacity
            style={[styles.settingRow, styles.lastRow]}
            onPress={handleClearHistory}
            disabled={alerts.length === 0}
          >
            <View style={styles.settingLabelContainer}>
              <Trash2 size={22} color={alerts.length === 0 ? colors.borderStrong : colors.alert} />
              <Text style={[styles.settingLabel, { color: alerts.length === 0 ? colors.textMuted : colors.text }]}>
                Clear Alert History
              </Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* My Zone */}
        <Text 
          style={[styles.sectionTitle, styles.sectionTitleSpaced]}
          onLayout={(e) => setZoneSectionY(e.nativeEvent.layout.y)}
        >
          ZONE
        </Text>
        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingLabelContainer}>
              <MapPin size={22} color={colors.live} />
              <View>
                <Text style={styles.settingLabel}>MY ZONE</Text>
                <Text style={styles.settingHint}>ONLY RING FOR YOUR REGION</Text>
              </View>
            </View>
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingLabelContainer}>
              <Crosshair size={22} color={colors.textSecondary} />
              <Text style={styles.settingLabel}>Detect my zone via GPS</Text>
            </View>
            <TouchableOpacity
              style={[styles.detectButton, detecting && { opacity: 0.6 }]}
              onPress={handleDetectZone}
              disabled={detecting}
            >
              {detecting ? (
                <ActivityIndicator size="small" color={colors.bg} />
              ) : (
                <Text style={styles.detectButtonText}>DETECT</Text>
              )}
            </TouchableOpacity>
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingLabelContainer}>
              <Globe size={22} color={colors.textSecondary} />
              <View style={{ flex: 1 }}>
                <Text style={styles.settingLabel}>Ring only for</Text>
                <Text style={styles.settingHint} numberOfLines={2}>
                  {myZoneCity}
                </Text>
              </View>
            </View>
          </View>

          <View style={styles.chipWrap}>
            <TouchableOpacity
              style={[styles.chip, homeZoneId == null && styles.chipActive]}
              onPress={() => selectZone(null)}
            >
              <Text style={homeZoneId == null ? styles.chipTextActive : styles.chipText}>ALL</Text>
            </TouchableOpacity>
            {(zones as Zone[] | undefined)?.map((zone) => {
              const active = homeZoneId === zone.id;
              return (
                <TouchableOpacity
                  key={zone.id}
                  style={[styles.chip, active && styles.chipActive]}
                  onPress={() => selectZone(zone.id)}
                >
                  <Text style={active ? styles.chipTextActive : styles.chipText}>{zone.city}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Explore */}
        <Text style={[styles.sectionTitle, styles.sectionTitleSpaced]}>EXPLORE</Text>
        <View style={styles.card}>
          <TouchableOpacity
            style={styles.settingRow}
            onPress={() => Linking.openURL("https://github.com/Gizano/QuakeGuard")}
          >
            <View style={styles.settingLabelContainer}>
              <Github size={22} color={colors.textSecondary} />
              <View>
                <Text style={styles.settingLabel}>GitHub repo</Text>
                <Text style={styles.settingHint}>Gizano/QuakeGuard</Text>
              </View>
            </View>
            <ExternalLink size={18} color={colors.textMuted} />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.settingRow, styles.lastRow]}
            onPress={() => Linking.openURL("https://giovanni-zanotti.is-a.dev/Projects/quakeguard.html")}
          >
            <View style={styles.settingLabelContainer}>
              <Globe size={22} color={colors.textSecondary} />
              <View>
                <Text style={styles.settingLabel}>QuakeGuard website</Text>
                <Text style={styles.settingHint}>Discover more about QuakeGuard!</Text>
              </View>
            </View>
            <ExternalLink size={18} color={colors.textMuted} />
          </TouchableOpacity>
        </View>

        <Text style={styles.versionFooter}>QuakeGuard v2.1.0</Text>
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
    card: {
      backgroundColor: c.surface,
      borderColor: c.border,
      borderWidth: 1,
      borderRadius: 16,
      padding: 16,
    },
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
    settingRow: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      paddingVertical: 16,
      borderBottomWidth: 1,
      borderBottomColor: c.border,
    },
    lastRow: { borderBottomWidth: 0 },
    settingLabelContainer: { flexDirection: "row", alignItems: "center", gap: 12, flex: 1 },
    settingLabel: { fontSize: 15, fontWeight: "500", color: c.text },
    settingHint: { fontSize: 11, color: c.textMuted, fontFamily: MONO, marginTop: 2, letterSpacing: 0.5 },
    detectButton: {
      backgroundColor: c.live,
      borderRadius: 8,
      paddingHorizontal: 14,
      paddingVertical: 8,
      minWidth: 74,
      alignItems: "center",
    },
    detectButtonText: { color: c.bg, fontSize: 12, fontWeight: "700", fontFamily: MONO, letterSpacing: 1 },
    chipWrap: { flexDirection: "row", flexWrap: "wrap", gap: 8, paddingTop: 12 },
    chip: {
      borderWidth: 1,
      borderColor: c.borderStrong,
      borderRadius: 20,
      paddingHorizontal: 12,
      paddingVertical: 6,
    },
    chipActive: { backgroundColor: c.live, borderColor: c.live },
    chipText: { color: c.textSecondary, fontSize: 12, fontFamily: MONO },
    chipTextActive: { color: c.bg, fontSize: 12, fontFamily: MONO, fontWeight: "700" },
    versionFooter: {
      marginTop: 24,
      textAlign: "center",
      fontSize: 11,
      color: c.textMuted,
      fontFamily: MONO,
      letterSpacing: 1,
    },
  });