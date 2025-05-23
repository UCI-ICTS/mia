// src/ auth.service.js

import axios from "axios";
import { store } from "../store";
import { getCSRFToken } from "../utils/csrf";

const MIADBURL = process.env.REACT_APP_MIADB;

const API = axios.create({ baseURL: `${MIADBURL}/mia/` });

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
  console.log(credentials, MIADBURL)
  const response = await API.post("/auth/login/", credentials);
  return response.data; // Return the full JSON response
};

// Log out function
const logout = async (credentials) => {
    await API.post("/auth/logout/", null, {
      headers: getAuthHeaders() 
    });
  };

// password reset received via email
const resetPassword = async (email) => {
  console.log("Service password reset: ", email);
  const response = await API.post("auth/password/reset/", {
    email,
  });
  return response.data;
};

// confirm password reset received via email
const confirmPasswordReset = async ({ uid, token, new_password }) => {
  const response = await API.post(
    "auth/password/confirm/",
    { uid, token, new_password },
    {
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      withCredentials: true,
    }
  );
  return response.data;
};

// activate user/create password received via email
const createPassword = async ({ uid, token, new_password }) => {
  const response = await API.post(
    "auth/users/activate/",
    { uid, token, new_password },
    {
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      withCredentials: true,
    }
  );
  return response.data;
};

export const authService = { login, logout, resetPassword, confirmPasswordReset, createPassword };

