// src/services/api.js
import axios from "axios";
import { store } from "../store"; // needed to read auth state

const KBIDBURL = process.env.REACT_APP_kbiDB;
  // change mia
const API = axios.create({
  baseURL: `${KBIDBURL}/mia/`, 
  withCredentials: true,
});

// Optional: Attach JWT token from Redux auth state if available
API.interceptors.request.use((config) => {
  const state = store.getState();
  const token = state.auth?.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default API;
