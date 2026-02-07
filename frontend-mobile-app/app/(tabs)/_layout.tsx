import { Tabs } from "expo-router";
import { Map, ShieldCheck } from "lucide-react-native";
import React from "react";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#dc2626", // Red color for active state
        tabBarInactiveTintColor: "#6b7280", // Gray color for inactive state
        tabBarStyle: {
          paddingBottom: 5,
          height: 60,
          borderTopWidth: 1,
          borderTopColor: "#e5e7eb",
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "600",
          marginBottom: 5,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Monitor",
          tabBarIcon: ({ color }) => <ShieldCheck size={28} color={color} />,
        }}
      />

      <Tabs.Screen
        name="map"
        options={{
          title: "Sensors",
          tabBarIcon: ({ color }) => <Map size={28} color={color} />,
        }}
      />
    </Tabs>
  );
}
