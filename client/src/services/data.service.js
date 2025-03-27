// src/services/data.service.js

import axios from "axios";
import { store } from "../store"; // Redux store to access auth state

const API = axios.create({ baseURL: "https://genomics.icts.uci.edu/mia" });

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
  await API.delete(`auth/users/${userId}/`, { headers: getAuthHeaders() });
};

// ✅ Get user invite link
const getInviteLink = async (username) => {
  const response = await API.get(`auth/consent-url/${username}/invite-link/`, { headers: getAuthHeaders() });
  return response.data;
};

// ✅ Generate new user invite link
const generateInviteLink = async (username) => {
  const response = await API.post(`auth/consent-url/`, {username}, { headers: getAuthHeaders() });
  return response.data;
};

// ✅ Submit Consent Response
const submitConsentResponse = async (invite_id, node_id ) => {
  const response = await API.get(`auth/consent-response/${invite_id}/`, 
    {params: {"node_id": node_id}
  });
  return response.data;
};


// ✅ Get consent from link
const getConsentByInvite = async (invite_id) => {
  const response = await API.get(`auth/consent/${invite_id}/`);
  return response.data
};

// ✅ Create a follow-up 
const createFollowUp = async ({email, follow_up_reason, follow_up_info}) => {
  console.log("Service ", {email, follow_up_reason, follow_up_info})
  const response = await API.post(`auth/follow_ups/`, {email, follow_up_reason, follow_up_info});
  return response
  };

// ✅ Fetch all follow-ups
const getFollowUps = async () => {
const response = await API.get("auth/follow_ups/", { headers: getAuthHeaders() });
return response.data;
};

// ✅ Mark a follow-up as resolved
const markFollowUpResolved = async (id) => {
await API.post(`/follow-ups/${id}/resolve`, {}, { headers: getAuthHeaders() });
};


// ✅ Fetch all scripts
const getScripts = async () => {
    const response = await API.get("/consentbot/scripts/", { headers: getAuthHeaders() });
    return response.data;
  };
  
  // ✅ Add a new script
  const addScript = async (scriptData) => {
    const response = await API.post("/consentbot/scripts/", scriptData, { headers: getAuthHeaders() });
    return response.data;
  };
  
  // ✅ Edit an existing script
  const editScript = async (id, updates) => {
    console.log(id, updates)
    const response = await API.put(`/consentbot/scripts/${id}/`, updates, { headers: getAuthHeaders() });
    return response.data;
  };
  
  // ✅ Delete a script
  const deleteScript = async (id) => {
    await API.delete(`/consentbot/scripts/${id}/`, { headers: getAuthHeaders() });
  };
  
export const dataService = {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  getInviteLink,
  generateInviteLink,
  getConsentByInvite,
  submitConsentResponse,
  createFollowUp,
  getFollowUps,
  markFollowUpResolved,
  getScripts,
  addScript,
  editScript,
  deleteScript
};
