import { create } from 'zustand';

export interface PairedDevice {
  publicKey: string;
  label: string;
  pairedAt: string;
}

interface DeviceStore {
  devices: PairedDevice[];
  addDevice: (publicKey: string, label: string) => void;
  removeDevice: (publicKey: string) => void;
  clearDevices: () => void;
}

export const useDeviceStore = create<DeviceStore>((set) => ({
  devices: [],
  addDevice: (publicKey, label) =>
    set((state) => {
      // Prevent duplicates
      if (state.devices.some((d) => d.publicKey === publicKey)) {
        return state;
      }
      return {
        devices: [
          ...state.devices,
          { publicKey, label, pairedAt: new Date().toISOString() },
        ],
      };
    }),
  removeDevice: (publicKey) =>
    set((state) => ({
      devices: state.devices.filter((d) => d.publicKey !== publicKey),
    })),
  clearDevices: () => set({ devices: [] }),
}));
