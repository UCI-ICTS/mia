// src/slices/consentSlice.js

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import consentService from "../services/consent.service";

// Thunks
export const fetchConsentByInvite = createAsyncThunk(
  "consent/fetchByInvite",
  async (invite_id, { rejectWithValue }) => {
    try {
      const data = await consentService.fetchConsentByInvite(invite_id);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const submitConsentResponse = createAsyncThunk(
  "consent/submitResponse",
  async (payload, { rejectWithValue }) => {
    try {
      const data = await consentService.submitConsentResponse(payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

export const submitConsentForm = createAsyncThunk(
  "consent/submitForm",
  async (payload, { rejectWithValue }) => {
    try {
      const data = await consentService.submitConsentResponse(payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || err.message);
    }
  }
);

const consentSlice = createSlice({
  name: "consent",
  initialState: {
    consent: null,
    chat: [],
    loading: false,
    error: null,
  },
  reducers: {
    clearConsentState: (state) => {
      state.consent = null;
      state.chat = [];
      state.loading = false;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchConsentByInvite.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchConsentByInvite.fulfilled, (state, action) => {
        state.loading = false;
        state.consent = action.payload;
        state.chat = action.payload.chat || [];
      })
      .addCase(fetchConsentByInvite.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      .addCase(submitConsentResponse.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitConsentResponse.fulfilled, (state, action) => {
        state.loading = false;
        state.chat = action.payload.chat || [];
        if (action.payload.consent) {
          state.consent = action.payload.consent;
        }
      })
      .addCase(submitConsentResponse.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      .addCase(submitConsentForm.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitConsentForm.fulfilled, (state, action) => {
        state.loading = false;
        state.chat = action.payload.chat || [];
        if (action.payload.consent) {
          state.consent = action.payload.consent;
        }
      })
      .addCase(submitConsentForm.rejected, (state, action) => {
        console.log(action.payload)
        state.loading = false;
        state.error = action.payload.error;
      });
  },
});

export const { clearConsentState } = consentSlice.actions;
export default consentSlice.reducer;
