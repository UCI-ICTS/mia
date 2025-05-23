// src/services/consent.service.js

import API from "./api";
import { getCSRFToken } from "../utils/csrf";

// ✅ Fetch Consent Session by Invite ID
const fetchConsentByInvite = async (invite_id) => {
  const response = await API.get(`consentbot/consent/${invite_id}/`, {
    headers: {
      "X-CSRFToken": getCSRFToken(),
    },
    withCredentials: true,
  });
  return response.data;
};

// ✅ Submit Consent Response (button or form)
const submitConsentResponse = async ({ invite_id, node_id, form_type, form_responses }) => {
  const payload = {
    invite_id,
    node_id,
  };
  if (form_type && form_responses) {
    payload.form_type = form_type;
    payload.form_responses = form_responses;
    const response = await API.post(`consentbot/consent-response/`, payload, {
        headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
        },
        withCredentials: true,
    });
    return response.data;
  } else {
    const response = await API.get(`consentbot/consent-response/${invite_id}/?node_id=${node_id}`, {
        headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
        },
        withCredentials: true,
    });
    return response.data;
  } 
};

const consentService = {
  fetchConsentByInvite,
  submitConsentResponse,
};

export default consentService;
