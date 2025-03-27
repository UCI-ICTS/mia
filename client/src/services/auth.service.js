// src/ auth.service.js

import axios from "axios";
import { store } from "../store";


const API = axios.create({ baseURL: "https://genomics.icts.uci.edu/mia" });

const getAuthHeaders = () => {
    const state = store.getState();
    const token = state.auth.accessToken;
  
    if (!token) {
      throw new Error("No authentication token found.");
    }
  
    return {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  };


// Log in function
const login = async (credentials) => {
  const response = await API.post("/auth/login/", credentials);
  return response.data; // Return the full JSON response
};

// Log out function
const logout = async (credentials) => {
    await API.post("/auth/logout/", null, {
      headers: getAuthHeaders() 
    });
  };

export const authService = { login, logout };
