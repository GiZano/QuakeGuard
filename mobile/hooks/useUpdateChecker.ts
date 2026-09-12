import { useEffect } from 'react';
import { Alert, Linking, Platform } from 'react-native';
import Constants from 'expo-constants';

const GITHUB_REPO = 'GiZano/QuakeGuard';

// Compare semantic versions (e.g. "2.1.1" > "2.0.2")
const isNewerVersion = (latest: string, current: string) => {
  const parse = (v: string) => v.replace(/^v/, '').split('.').map(Number);
  const l = parse(latest);
  const c = parse(current);
  
  for (let i = 0; i < 3; i++) {
    if ((l[i] || 0) > (c[i] || 0)) return true;
    if ((l[i] || 0) < (c[i] || 0)) return false;
  }
  return false;
};

export function useUpdateChecker() {
  useEffect(() => {
    const checkForUpdates = async () => {
      try {
        const currentVersion = Constants.expoConfig?.version || '1.0.0';
        
        // Fetch the latest release from GitHub API
        const response = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`);
        const data = await response.json();
        
        const latestVersion = data.tag_name;
        
        if (latestVersion && isNewerVersion(latestVersion, currentVersion)) {
          // Find the APK asset in the release
          const apkAsset = data.assets?.find((asset: any) => asset.name.endsWith('.apk'));
          const downloadUrl = apkAsset ? apkAsset.browser_download_url : data.html_url;

          Alert.alert(
            "Aggiornamento Disponibile",
            `È disponibile una nuova versione di QuakeGuard (${latestVersion}). Vuoi scaricarla ora?`,
            [
              { text: "Più tardi", style: "cancel" },
              { 
                text: "Scarica", 
                onPress: () => {
                  Linking.openURL(downloadUrl);
                } 
              }
            ]
          );
        }
      } catch (error) {
        console.warn("Update check failed:", error);
      }
    };

    // Only check for APK updates on Android. 
    // On iOS we'd use TestFlight/App Store, so this is mostly for the open-source sideloading.
    if (Platform.OS === 'android') {
      checkForUpdates();
    }
  }, []);
}
