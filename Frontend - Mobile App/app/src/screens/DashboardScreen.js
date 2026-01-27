import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';

const DashboardScreen = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState(null);
  const API_URL = process.env.EXPO_PUBLIC_API_URL;

  const fetchStats = async () => {
    try {
      // Fetching stats from backend
      const response = await fetch(`${API_URL}/stats/zones`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.log('Error fetching stats:', error);
    }
  };

  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await fetchStats();
    setRefreshing(false);
  }, []);

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard Rilevamenti</Text>
      </View>

      {/* Summary Cards */}
      <View style={styles.cardContainer}>
        {stats ? (
          stats.map((zone, index) => (
            <View key={index} style={styles.card}>
              <Text style={styles.zoneName}>{zone.city} (ID: {zone.zone_id})</Text>
              <View style={styles.row}>
                <Text style={styles.label}>Sensori Attivi:</Text>
                <Text style={styles.value}>{zone.active_misurators} / {zone.total_misurators}</Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>Ultima Attività:</Text>
                <Text style={styles.value}>
                  {zone.last_misuration ? new Date(zone.last_misuration).toLocaleTimeString() : 'N/A'}
                </Text>
              </View>
            </View>
          ))
        ) : (
          <Text style={styles.loadingText}>Caricamento dati...</Text>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#ecf0f1' },
  header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#ddd', marginTop: 30 },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: '#2c3e50' },
  cardContainer: { padding: 15 },
  card: { backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 15, elevation: 3 },
  zoneName: { fontSize: 18, fontWeight: 'bold', marginBottom: 10, color: '#E74C3C' },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 5 },
  label: { color: '#7f8c8d' },
  value: { fontWeight: 'bold', color: '#2c3e50' },
  loadingText: { textAlign: 'center', marginTop: 20, color: '#7f8c8d' }
});

export default DashboardScreen;