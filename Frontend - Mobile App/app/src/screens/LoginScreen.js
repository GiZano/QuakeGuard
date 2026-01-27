import React, { useState } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, 
  ActivityIndicator, KeyboardAvoidingView, Platform 
} from 'react-native';
import * as Location from 'expo-location'; // Module for GPS permissions

const LoginScreen = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // Load API URL from .env file
  const API_URL = process.env.EXPO_PUBLIC_API_URL;

  /**
   * Request Location Permissions
   * Must be called immediately after successful login/bypass.
   */
  const requestPermissionsAndNavigate = async () => {
    try {
      // Request permission
      let { status } = await Location.requestForegroundPermissionsAsync();
      
      if (status !== 'granted') {
        Alert.alert(
          'Permesso Negato', 
          'L\'app ha bisogno della posizione per visualizzare la mappa sismica.'
        );
        // We navigate anyway, but map features might be limited
      }
      
      // Navigate to the Tab Navigator (Main App) replacing the Login screen
      navigation.replace('MainApp');

    } catch (error) {
      console.error("Permission Error:", error);
      navigation.replace('MainApp');
    }
  };

  const handleLogin = async () => {
    setLoading(true);

    // --- BYPASS LOGIC ---
    if (email.trim() === 'admin@example.com' && password === 'admin') {
      console.log('Admin Bypass Triggered');
      // Simulate network delay for realism
      setTimeout(async () => {
        setLoading(false);
        await requestPermissionsAndNavigate();
      }, 500);
      return;
    }

    // --- STANDARD API LOGIC ---
    if (!email || !password) {
      Alert.alert('Errore', 'Inserisci email e password');
      setLoading(false);
      return;
    }

    try {
      console.log(`Connecting to: ${API_URL}`);
      // TODO: Implement real fetch to backend /login endpoint here
      await new Promise(resolve => setTimeout(resolve, 1500)); // Mock delay
      Alert.alert('Errore', 'Utente non trovato (Usa il bypass admin)');
    } catch (error) {
      Alert.alert('Errore di Connessione', 'Impossibile contattare il server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <View style={styles.formContainer}>
        <Text style={styles.title}>Sismografo IoT 🌋</Text>
        <Text style={styles.subtitle}>Accesso Rete di Monitoraggio</Text>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>Email</Text>
          <TextInput
            style={styles.input}
            placeholder="admin@example.com"
            autoCapitalize="none"
            keyboardType="email-address"
            value={email}
            onChangeText={setEmail}
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>Password</Text>
          <TextInput
            style={styles.input}
            placeholder="admin"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />
        </View>

        <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>ACCEDI</Text>}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f0f0', justifyContent: 'center', padding: 20 },
  formContainer: { backgroundColor: '#fff', padding: 25, borderRadius: 15, elevation: 5 },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginBottom: 5, color: '#2c3e50' },
  subtitle: { fontSize: 14, textAlign: 'center', marginBottom: 30, color: '#7f8c8d' },
  inputContainer: { marginBottom: 15 },
  label: { fontSize: 12, fontWeight: 'bold', marginBottom: 5, color: '#34495e' },
  input: { height: 50, borderColor: '#bdc3c7', borderWidth: 1, borderRadius: 8, paddingHorizontal: 15, backgroundColor: '#fafafa' },
  button: { backgroundColor: '#E74C3C', height: 55, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 10 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});

export default LoginScreen;