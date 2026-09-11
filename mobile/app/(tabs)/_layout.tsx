import { Tabs } from "expo-router";
import { Map, ShieldCheck, Settings, Network } from "lucide-react-native";
import React from "react";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAppTheme } from "../../theme/useTheme";
import { MONO } from "../../theme";

const MonitorIcon = ({ color }: { color: string }) => <ShieldCheck size={28} color={color} />;
const MapIcon = ({ color }: { color: string }) => <Map size={28} color={color} />;
const DevicesIcon = ({ color }: { color: string }) => <Network size={28} color={color} />;
const SettingsIcon = ({ color }: { color: string }) => <Settings size={28} color={color} />;

export default function TabLayout() {
  const insets = useSafeAreaInsets();
  const { colors } = useAppTheme();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.alert,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.bg,
          borderTopColor: colors.border,
          paddingBottom: 5 + insets.bottom,
          height: 60 + insets.bottom,
          borderTopWidth: 1,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: "700",
          marginBottom: 5,
          fontFamily: MONO,
          letterSpacing: 1,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Monitor",
          tabBarIcon: MonitorIcon,
        }}
      />

      <Tabs.Screen
        name="map"
        options={{
          title: "Sensors",
          tabBarIcon: MapIcon,
        }}
      />

      <Tabs.Screen
        name="devices"
        options={{
          title: "Devices",
          tabBarIcon: DevicesIcon,
        }}
      />

      <Tabs.Screen
        name="settings"
        options={{
          title: "Settings",
          tabBarIcon: SettingsIcon,
        }}
      />
    </Tabs>
  );
}
