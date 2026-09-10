import FontAwesome from "@expo/vector-icons/FontAwesome";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";
import { WebSocketProvider } from "../context/WebSocketContext";
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { FONTS } from "../theme";

import { useUpdateChecker } from "../hooks/useUpdateChecker";

// 1. Import TanStack Query essentials
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

SplashScreen.preventAutoHideAsync();

// 2. Instantiate the QueryClient
// This holds the global cache for all your network requests
const queryClient = new QueryClient();

export default function RootLayout() {
  useUpdateChecker();

  const [loaded, error] = useFonts({
    ...FontAwesome.font,
    [FONTS.mono]: require("../assets/fonts/SpaceMono-Regular.ttf"),
  });

  useEffect(() => {
    if (error) throw error;
  }, [error]);

  useEffect(() => {
    if (loaded) {
      SplashScreen.hideAsync();
    }
  }, [loaded]);

  if (!loaded) return null;

  return (
    // 3. Wrap the app with the QueryClientProvider
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <WebSocketProvider>
          <Stack>
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          </Stack>
        </WebSocketProvider>
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}