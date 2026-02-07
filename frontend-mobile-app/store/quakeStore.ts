import { Vibration } from "react-native";
import { create } from "zustand";
import { API_BASE_URL } from "../constants/config";

// ------------------------------------------------------------------
// Interfaces
// ------------------------------------------------------------------

interface Alert {
  id: number;
  timestamp: string; // ISO 8601 format
  severity: string;
}

interface Sensor {
  id: number;
  lat: number;
  lon: number;
  status: "Active" | "Inactive";
}

interface QuakeState {
  // State variables
  systemStatus: "SECURE" | "ALERT";
  sensors: Sensor[];
  lastAlertTime: string | null;

  // Actions
  fetchSensors: () => Promise<void>;
  startMonitoring: () => void;
  stopMonitoring: () => void;
}

// ------------------------------------------------------------------
// Store Implementation
// ------------------------------------------------------------------

// External reference for the interval timer to manage lifecycle outside the hook
let pollingInterval: NodeJS.Timeout | null = null;

export const useQuakeStore = create<QuakeState>((set, get) => ({
  systemStatus: "SECURE",
  sensors: [],
  lastAlertTime: null,

  /**
   * Fetches the list of sensors from the backend.
   */
  fetchSensors: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/misurators/`);
      if (!response.ok) throw new Error("Network response was not ok");
      const data: Sensor[] = await response.json();
      set({ sensors: data });
    } catch (error) {
      console.error("[QuakeStore] Error fetching sensors:", error);
    }
  },

  /**
   * Starts the polling mechanism to check for recent alerts.
   * Polls every 2 seconds.
   */
  startMonitoring: () => {
    if (pollingInterval) return; // Prevent multiple intervals

    pollingInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/zones/1/alerts`);
        if (!response.ok) return; // Silent fail on network error to keep polling

        const alerts: Alert[] = await response.json();

        const currentStatus = get().systemStatus;
        let newStatus: "SECURE" | "ALERT" = "SECURE";
        let latestAlertTime = null;

        if (alerts.length > 0) {
          // Alerts are assumed to be sorted or we take the last pushed
          const latestAlert = alerts[alerts.length - 1];
          const alertTime = new Date(latestAlert.timestamp).getTime();
          const now = new Date().getTime();
          const diffSeconds = (now - alertTime) / 1000;

          // Threshold: Alert is considered active if less than 60 seconds old
          if (diffSeconds < 60) {
            newStatus = "ALERT";
            latestAlertTime = latestAlert.timestamp;
          }
        }

        // Trigger haptic feedback on state transition to ALERT
        if (newStatus === "ALERT" && currentStatus === "SECURE") {
          Vibration.vibrate([0, 500, 200, 500]); // Wait 0ms, Vibrate 500ms, Wait 200ms, Vibrate 500ms
        }

        set({ systemStatus: newStatus, lastAlertTime: latestAlertTime });
      } catch (error) {
        console.warn("[QuakeStore] Polling error:", error);
      }
    }, 2000);
  },

  /**
   * Clears the polling interval.
   */
  stopMonitoring: () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  },
}));
