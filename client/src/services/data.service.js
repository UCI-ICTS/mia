// src/services/data.service.js

import API from "./api";

// Users
const fetchUsers = async () => {
  const response = await API.get(`auth/users/`);
  return response.data;
};

const addUser = async (data) => {
  const response = await API.post(`auth/users/`, data);
  return response.data;
};

const updateUser = async (username, updates) => {
  const response = await API.put(`auth/users/${username}/`, updates);
  return response.data;
};

const deleteUser = async (username) => {
  const response = await API.delete(`auth/users/${username}/`);
  return response.data;
};

const getInviteLink = async (username) => {
  const response = await API.get(`consentbot/consent-url/${username}/invite-link/`);
  return response.data;
};

const generateInviteLink = async (username) => {
  const response = await API.post(`consentbot/consent-url/`, { username });
  return response.data;
};

// Scripts
const fetchConsentScripts = async () => {
  const response = await API.get(`consentbot/scripts/`);
  return response.data;
};

const addScript = async (data) => {
  const response = await API.post(`consentbot/scripts/`, data);
  return response.data;
};

const editScript = async (id, updates) => {
  const response = await API.put(`consentbot/scripts/${id}/`, updates);
  return response.data;
};

const deleteScript = async (id) => {
  const response = await API.delete(`consentbot/scripts/${id}/`);
  return response.data;
};

// Follow-ups
const fetchFollowUps = async () => {
  const response = await API.get(`auth/follow-ups/`);
  return response.data;
};

const createFollowUp = async (data) => {
  const response = await API.post(`auth/follow-ups/`, data);
  return response.data;
};

const resolveFollowUp = async (id) => {
  const response = await API.patch(`auth/follow-ups/${id}/`, { resolved: true });
  return response.data;
};

const dataService = {
  fetchUsers,
  addUser,
  updateUser,
  deleteUser,
  getInviteLink,
  generateInviteLink,
  fetchConsentScripts,
  addScript,
  editScript,
  deleteScript,
  fetchFollowUps,
  createFollowUp,
  resolveFollowUp,
};

export default dataService;
