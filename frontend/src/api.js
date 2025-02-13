// src/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add interceptors
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const loginUser = async (username, password) => {
  try {
    const response = await api.post('/login', {}, {
      auth: { username, password }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Login failed');
  }
};

// CSV API
export const fetchCSV = async () => {
  try {
    const response = await api.get('/fetch_csv');
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch CSV data');
  }
};

// Secure Data Example
export const fetchSecureData = async () => {
  try {
    const response = await api.get('/secure-data');
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Request failed');
  }
};