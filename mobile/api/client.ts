import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, IOT_API_KEY } from '../constants/config'; 

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': IOT_API_KEY 
  },
});

apiClient.interceptors.request.use(async (config) => {
  try {
    const dynamicUrl = await AsyncStorage.getItem('CLOUD_TUNNEL_URL');
    if (dynamicUrl) {
      config.baseURL = dynamicUrl;
    }
  } catch (e) {
    console.error("Failed to fetch dynamic URL", e);
  }
  return config;
});
