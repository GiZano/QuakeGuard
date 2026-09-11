import AsyncStorage from '@react-native-async-storage/async-storage';
import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  useCallback,
} from "react";
import { Vibration, Platform } from "react-native";
import * as Device from "expo-device";
import { API_BASE_URL, MOBILE_WS_TOKEN } from "../constants/config";
import { useAlertStore } from '../store/useAlertStore';
import { usePreferencesStore } from '../store/usePreferencesStore';
import { playAlarm } from "../audio/alarm";

let Notifications: any = null;
try {
  Notifications = require("expo-notifications");
  // --- NOTIFICATION HANDLER ---
  Notifications.setNotificationHandler({
    handleNotification: async () => {
      const enabled = usePreferencesStore.getState().notificationsEnabled;
      return {
        shouldShowBanner: enabled,
        shouldShowList: enabled,
        shouldPlaySound: enabled,
        shouldSetBadge: false,
      };
    },
  });
} catch (e) {
  console.warn("expo-notifications disabled (likely Expo Go SDK 53+)", e);
}

// --- TYPES & INTERFACES ---
export interface AlertMessage {
  type: string;
  alert_id?: number;
  zone_id: number;
  magnitude: number;
  message: string;
  latitude?: number;
  longitude?: number;
  origin_time?: string;
  timestamp: string;
}

export interface EmergencyReportMessage {
  type: "EMERGENCY_REPORT";
  alert_id: number;
  report_id: number;
  zone_id: number;
  magnitude: number;
  status: "COMPLETED" | "FAILED";
  summary?: string;
  recommendations?: string[];
  timestamp: string;
}

interface WebSocketContextType {
  isConnected: boolean;
  lastAlert: AlertMessage | null;
  lastReport: EmergencyReportMessage | null;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

// --- CONSTANTS ---
const SOS_VIBRATION_PATTERN = [
  0, 200, 100, 200, 100, 200, 
  300, 500, 300, 500, 300, 500, 
  300, 200, 100, 200, 100, 200, 
];

const MAX_RECONNECT_DELAY = 30000;

export const WebSocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastAlert, setLastAlert] = useState<AlertMessage | null>(null);
  const [lastReport, setLastReport] = useState<EmergencyReportMessage | null>(null);
  
  // Bring in the offline mode flag
  const isOfflineMode = usePreferencesStore((state) => state.isOfflineMode);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null); 
  const reconnectAttempts = useRef<number>(0);
  
  // Track intentional closures so the onclose handler doesn't aggressively reconnect
  const intentionalClose = useRef<boolean>(false);

  useEffect(() => {
    const registerForPushNotificationsAsync = async () => {
      if (!Notifications) return;
      if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('default', {
          name: 'default',
          importance: Notifications.AndroidImportance.MAX,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#FF231F7C',
        });
      }
      if (Device.isDevice) {
        // SDK 54: expo-notifications no longer depends on expo-modules-core, so
        // its NotificationPermissionsStatus typings resolve empty. Read the
        // permission via `granted`, which is present at runtime.
        const existingGranted = (await Notifications.getPermissionsAsync() as any).granted;
        let granted = existingGranted;
        if (!existingGranted) {
          granted = (await Notifications.requestPermissionsAsync() as any).granted;
        }
        if (!granted) {
          console.warn('Failed to get push token for push notification!');
          return;
        }
      }
    };
    registerForPushNotificationsAsync();
  }, []);
  
  const handleEmergencyReport = useCallback((report: EmergencyReportMessage, ringsForZone: (zoneId: number) => boolean) => {
    console.log("🤖 AI REPORT RECEIVED:", report);
    setLastReport(report);
    useAlertStore.getState().addReport(report);

    if (ringsForZone(report.zone_id) && Notifications) {
      Notifications.scheduleNotificationAsync({
        content: {
          title: report.status === "COMPLETED" ? "🤖 AI Emergency Report" : "🤖 AI Report Unavailable",
          body:
            report.status === "COMPLETED"
              ? report.summary ?? "Emergency report generated."
              : "The AI report could not be generated. Contact local authorities.",
          sound: true,
          priority: Notifications.AndroidNotificationPriority.MAX,
        },
        trigger: null,
      });
    }
  }, []);

  const handleAlert = useCallback((alert: AlertMessage, ringsForZone: (zoneId: number) => boolean) => {
    console.log("⚡ ALERT RECEIVED:", alert);
    setLastAlert(alert);
    useAlertStore.getState().addAlert(alert);

    if ((alert.type === "CRITICAL" || alert.type === "TRIANGULATED") && ringsForZone(alert.zone_id)) {
      Vibration.vibrate(SOS_VIBRATION_PATTERN);
      playAlarm(15000);
      if (Notifications) {
        Notifications.scheduleNotificationAsync({
          content: {
            title: alert.type === "TRIANGULATED" ? "🚨 TRIANGULATED ALERT: EPICENTER FOUND" : "⚠️ CRITICAL SEISMIC ALERT",
            body: `Magnitude ${alert.magnitude.toFixed(1)} detected. ${alert.message}`,
            sound: true,
            priority: Notifications.AndroidNotificationPriority.MAX,
          },
          trigger: null,
        });
      }
    }
  }, []);
  
  const connect = useCallback(async function doConnect() {
    if (usePreferencesStore.getState().isOfflineMode) return;
    
    // FIX: Also block when the socket is in "CONNECTING" (0) state,
    // otherwise React creates two nearly simultaneously.
    if (ws.current?.readyState === WebSocket.OPEN || ws.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    intentionalClose.current = false;
    const dynamicUrl = await AsyncStorage.getItem('CLOUD_TUNNEL_URL');
    const baseUrl = dynamicUrl || API_BASE_URL;
    const wsUrl = `${baseUrl.replace("http", "ws")}/ws/alerts?token=${MOBILE_WS_TOKEN}`;
    console.log(`🔌 Attempting WS Connection: ${wsUrl}`);

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("✅ WS Connected Successfully");
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };

    ws.current.onmessage = (event: WebSocketMessageEvent) => {
      try {
        const message: any = JSON.parse(event.data);
        const { notificationsEnabled, homeZoneId } = usePreferencesStore.getState();

        // The operator can set a home zone so the phone only rings for their
        // own area — a quake on the other side of the world stays silently
        // visible in the activity feed.
        const ringsForZone = (zoneId: number): boolean =>
          notificationsEnabled && (homeZoneId == null || zoneId === homeZoneId);

        if (message.type === "EMERGENCY_REPORT") {
          handleEmergencyReport(message, ringsForZone);
        } else {
          handleAlert(message, ringsForZone);
        }
      } catch (err) {
        console.error("❌ Error parsing WS message:", err);
      }
    };

    ws.current.onclose = () => {
      console.log("❌ WS Disconnected");
      setIsConnected(false);

      // Do not attempt to reconnect if the user intentionally went offline
      if (intentionalClose.current) return;

      const delay = Math.min(
        1000 * Math.pow(2, reconnectAttempts.current),
        MAX_RECONNECT_DELAY
      );
      
      console.log(`⏳ Reconnecting in ${delay / 1000} seconds...`);
      reconnectTimeout.current = setTimeout(() => {
        reconnectAttempts.current += 1;
        doConnect();
      }, delay);
    };

    ws.current.onerror = (error: Event) => {
      console.error("⚠️ WS Error:", error);
    };
  }, [handleEmergencyReport, handleAlert]);

  // 💡 THE NEW WATCHER: React to the offline toggle changing
  useEffect(() => {
    if (isOfflineMode) {
      console.log("🛑 Offline Mode Activated. Shutting down WS...");
      intentionalClose.current = true;
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.close();
        ws.current = null; // Pulizia profonda
      }
    } else {
      console.log("🟢 Online Mode Activated. Booting up WS...");
      connect();
    }

    // Cleanup function for when the app is closed
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, [isOfflineMode, connect]);
  
  // 💡 THE SECOND useEffect(() => { connect() }) HAS BEEN COMPLETELY REMOVED!

  return (
    <WebSocketContext.Provider
      value={useMemo(
        () => ({ isConnected, lastAlert, lastReport }),
        [isConnected, lastAlert, lastReport]
      )}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
};