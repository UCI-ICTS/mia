// src/services/data.service.js
import axios from "axios";
import { store } from "../store"; // Redux store to access auth state

const API = axios.create({ baseURL: "http://localhost:8000/mia" });

const getAuthHeaders = () => {
  const state = store.getState();
  const token = state.auth.accessToken;

  if (!token) {
    throw new Error("No authentication token found.");
  }

  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
};

// ✅ Fetch all users
const getUsers = async () => {
  const response = await API.get("auth/users/", { headers: getAuthHeaders() });
  return response.data;
};

// ✅ Create a new user
const createUser = async (userData) => {
  const response = await API.post("auth/users/", userData, { headers: getAuthHeaders() });
  return response.data;
};

// ✅ Update an existing user
const updateUser = async (userData) => {
  const response = await API.put(`auth/users/${userData.username}/`, userData, { headers: getAuthHeaders() });
  return response.data;
};

// ✅ Delete a user
const deleteUser = async (userId) => {
  await API.delete(`auth/users/${userId}`, { headers: getAuthHeaders() });
};

// ✅ Get user invite link
const getInviteLink = async (userId) => {
  const response = await API.get(`auth/users/${userId}/invite-link`, { headers: getAuthHeaders() });
  return response.data.link;
  
};
// ✅ Fetch all follow-ups
const getFollowUps = async () => {
const response = await API.get("/follow-ups", { headers: getAuthHeaders() });
return response.data;
};

// ✅ Mark a follow-up as resolved
const markFollowUpResolved = async (id) => {
await API.post(`/follow-ups/${id}/resolve`, {}, { headers: getAuthHeaders() });
};


// ✅ Fetch all scripts
const getScripts = async () => {
    const response = await API.get("/scripts", { headers: getAuthHeaders() });
    return response.data;
  };
  
  // ✅ Add a new script
  const addScript = async (scriptData) => {
    const response = await API.post("/scripts", scriptData, { headers: getAuthHeaders() });
    return response.data;
  };
  
  // ✅ Edit an existing script
  const editScript = async (id, updates) => {
    const response = await API.put(`/scripts/${id}`, updates, { headers: getAuthHeaders() });
    return response.data;
  };
  
  // ✅ Delete a script
  const deleteScript = async (id) => {
    await API.delete(`/scripts/${id}`, { headers: getAuthHeaders() });
  };
  
export const dataService = {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  getInviteLink,
  getFollowUps,
  markFollowUpResolved,
  getScripts,
  addScript,
  editScript,
  deleteScript
};
