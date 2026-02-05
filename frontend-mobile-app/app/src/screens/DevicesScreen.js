import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, TextInput, Alert, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const DevicesScreen = () => {
  const [devices, setDevices] = useState([]);
  const [newDeviceId, setNewDeviceId] = useState('');
  const [selectedDevice, setSelectedDevice] = useState(null);
  const API_URL = process.env.EXPO_PUBLIC_API_URL;

  // Mock Fetch Devices
  const fetchDevices = async () => {
    // In real app: fetch(`${API_URL}/misurators/`)
    // Mock data for UI demonstration:
    setDevices([
      { id: 1, zone_id: 1, active: true, latitude: 41.9028, longitude: 12.4964 },
      { id: 2, zone_id: 1, active: false, latitude: 41.9030, longitude: 12.4970 },
    ]);
  };

  const registerDevice = async () => {
    if (!newDeviceId) return;
    try {
      // Example POST logic
      // await fetch(`${API_URL}/misurators/`, { method: 'POST', body: ... })
      Alert.alert('Successo', `Dispositivo ID ${newDeviceId} registrato (Simulazione)`);
      setNewDeviceId('');
      fetchDevices(); // Refresh list
    } catch (error) {
      Alert.alert('Errore', 'Impossibile registrare il dispositivo');
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const renderDeviceItem = ({ item }) => (
    <TouchableOpacity style={styles.deviceItem} onPress={() => setSelectedDevice(item)}>
      <Ionicons name="hardware-chip" size={24} color={item.active ? "green" : "gray"} />
      <View style={styles.deviceInfo}>
        <Text style={styles.deviceName}>Sensore #{item.id}</Text>
        <Text style={styles.deviceSub}>Zona: {item.zone_id} | GPS: {item.latitude.toFixed(2)}, {item.longitude.toFixed(2)}</Text>
      </View>
      <Ionicons name="chevron-forward" size={20} color="#ccc" />
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Dispositivi Registrati</Text>
      </View>

      {/* Registration Area */}
      <View style={styles.registerContainer}>
        <TextInput
          style={styles.input}
          placeholder="Inserisci ID Dispositivo (DB)"
          value={newDeviceId}
          onChangeText={setNewDeviceId}
          keyboardType="numeric"
        />
        <TouchableOpacity style={styles.addButton} onPress={registerDevice}>
          <Text style={styles.addButtonText}>REGISTRA</Text>
        </TouchableOpacity>
      </View>

      {/* Device List */}
      <FlatList
        data={devices}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderDeviceItem}
        contentContainerStyle={styles.list}
      />

      {/* Simple Modal for Device Dashboard */}
      <Modal visible={!!selectedDevice} animationType="slide" transparent={true}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Dashboard Sensore #{selectedDevice?.id}</Text>
            <Text>Stato: {selectedDevice?.active ? 'Attivo' : 'Inattivo'}</Text>
            <View style={styles.chartPlaceholder}>
              <Text style={{color: '#fff'}}>Grafico Misurazioni (Placeholder)</Text>
            </View>
            <TouchableOpacity style={styles.closeButton} onPress={() => setSelectedDevice(null)}>
              <Text style={styles.closeText}>CHIUDI</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, paddingTop: 50, backgroundColor: '#fff' },
  title: { fontSize: 22, fontWeight: 'bold' },
  registerContainer: { flexDirection: 'row', padding: 15, backgroundColor: '#fff', marginTop: 10 },
  input: { flex: 1, borderColor: '#ddd', borderWidth: 1, borderRadius: 8, padding: 10, marginRight: 10 },
  addButton: { backgroundColor: '#2980b9', justifyContent: 'center', paddingHorizontal: 20, borderRadius: 8 },
  addButtonText: { color: '#fff', fontWeight: 'bold' },
  list: { padding: 15 },
  deviceItem: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', padding: 15, marginBottom: 10, borderRadius: 10, elevation: 2 },
  deviceInfo: { flex: 1, marginLeft: 15 },
  deviceName: { fontWeight: 'bold', fontSize: 16 },
  deviceSub: { color: 'gray', fontSize: 12 },
  modalContainer: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 20 },
  modalContent: { backgroundColor: '#fff', padding: 20, borderRadius: 15, alignItems: 'center' },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 20 },
  chartPlaceholder: { width: '100%', height: 150, backgroundColor: '#34495e', justifyContent: 'center', alignItems: 'center', marginVertical: 20, borderRadius: 10 },
  closeButton: { marginTop: 10, padding: 10 },
  closeText: { color: '#e74c3c', fontWeight: 'bold' }
});

export default DevicesScreen;