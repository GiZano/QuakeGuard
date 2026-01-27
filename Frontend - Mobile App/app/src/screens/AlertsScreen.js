import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';

const AlertsScreen = () => {
  const [filter, setFilter] = useState('day'); // hour, day, week, month

  // Mock Alerts Data
  const alerts = [
    { id: 1, zone: 'Roma Centro', time: new Date().toISOString(), severity: 'HIGH' },
    { id: 2, zone: 'Napoli Nord', time: new Date(Date.now() - 86400000).toISOString(), severity: 'MEDIUM' },
  ];

  const FilterButton = ({ title, value }) => (
    <TouchableOpacity 
      style={[styles.filterBtn, filter === value && styles.filterBtnActive]} 
      onPress={() => setFilter(value)}
    >
      <Text style={[styles.filterText, filter === value && styles.filterTextActive]}>{title}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Registro Allarmi</Text>
        <View style={styles.filterContainer}>
          <FilterButton title="1H" value="hour" />
          <FilterButton title="24H" value="day" />
          <FilterButton title="7D" value="week" />
          <FilterButton title="30D" value="month" />
        </View>
      </View>

      <FlatList
        data={alerts}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.alertItem}>
            <View style={[styles.indicator, { backgroundColor: item.severity === 'HIGH' ? '#e74c3c' : '#f1c40f' }]} />
            <View style={styles.content}>
              <Text style={styles.alertTitle}>Rilevamento Sismico - {item.zone}</Text>
              <Text style={styles.alertTime}>{new Date(item.time).toLocaleString()}</Text>
            </View>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.emptyText}>Nessun allarme nel periodo selezionato.</Text>}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, paddingTop: 50, backgroundColor: '#fff', borderBottomWidth: 1, borderColor: '#eee' },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 15 },
  filterContainer: { flexDirection: 'row', justifyContent: 'space-between' },
  filterBtn: { paddingVertical: 6, paddingHorizontal: 15, borderRadius: 20, backgroundColor: '#f0f0f0' },
  filterBtnActive: { backgroundColor: '#2c3e50' },
  filterText: { color: '#7f8c8d', fontWeight: 'bold' },
  filterTextActive: { color: '#fff' },
  alertItem: { flexDirection: 'row', backgroundColor: '#fff', padding: 15, marginHorizontal: 15, marginTop: 10, borderRadius: 10, elevation: 1 },
  indicator: { width: 5, borderRadius: 5, marginRight: 15 },
  content: { flex: 1 },
  alertTitle: { fontWeight: 'bold', fontSize: 16, color: '#2c3e50' },
  alertTime: { color: 'gray', marginTop: 5, fontSize: 12 },
  emptyText: { textAlign: 'center', marginTop: 30, color: 'gray' }
});

export default AlertsScreen;