import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

// Import Screens
import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
// import MapScreen from './src/screens/MapScreen'; // <--- RIMOSSO TEMPORANEAMENTE
import DevicesScreen from './src/screens/DevicesScreen';
import AlertsScreen from './src/screens/AlertsScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

/**
 * Main Application Tabs (Visible after Login)
 */
function AppTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Misurazioni') {
            iconName = focused ? 'stats-chart' : 'stats-chart-outline';
          } else if (route.name === 'Dispositivi') {
            iconName = focused ? 'hardware-chip' : 'hardware-chip-outline';
          } else if (route.name === 'Alert') {
            iconName = focused ? 'warning' : 'warning-outline';
          }
          // Icona mappa rimossa

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#E74C3C',
        tabBarInactiveTintColor: 'gray',
      })}
    >
      <Tab.Screen name="Misurazioni" component={DashboardScreen} />
      
      {/* <Tab.Screen name="Mappa" component={MapScreen} /> 
      */}
      
      <Tab.Screen name="Dispositivi" component={DevicesScreen} />
      <Tab.Screen name="Alert" component={AlertsScreen} />
    </Tab.Navigator>
  );
}

/**
 * Root Navigator
 */
export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator initialRouteName="Login">
          {/* Auth Screen */}
          <Stack.Screen 
            name="Login" 
            component={LoginScreen} 
            options={{ headerShown: false }} 
          />
          
          {/* Main App Container (Tabs) */}
          <Stack.Screen 
            name="MainApp" 
            component={AppTabs} 
            options={{ headerShown: false }} 
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}