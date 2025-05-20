
// src/slices/dataSlice.js

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import dataService from "../services/data.service";
import { message } from "antd";

const initialState = {
  participants: [],
  staff: [],
  scripts: [],
  followUps: [],
  loading: false,
  error: null,
};

// --- Thunks ---
export const fetchUsers = createAsyncThunk("data/fetchUsers", async (_, thunkAPI) => {
  try {
    return await dataService.fetchUsers();
  } catch (error) {
    message.error("Failed to fetch users.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const addUser = createAsyncThunk("data/addUser", async (userData, { rejectWithValue }) => {
  try {
    const res = await dataService.addUser(userData);
    message.success("User added successfully");
    return res;
  } catch (error) {
    message.error("Error adding user");
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const updateUser = createAsyncThunk("data/updateUser", async ({ username, updates }, { rejectWithValue }) => {
  try {
    const res = await dataService.updateUser(username, updates);
    message.success("User updated successfully");
    return res;
  } catch (error) {
    message.error("Error updating user");
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const deleteUser = createAsyncThunk("data/deleteUser", async (username, { rejectWithValue }) => {
  try {
    await dataService.deleteUser(username);
    message.success("User deleted successfully");
    return username;
  } catch (error) {
    message.error("Error deleting user");
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const generateInviteLink = createAsyncThunk("data/generateInviteLink", async (username, { rejectWithValue }) => {
  try {
    const res = await dataService.generateInviteLink(username);
    return res;
  } catch (error) {
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const getInviteLink = createAsyncThunk("data/getInviteLink", async (username, { rejectWithValue }) => {
  try {
    return await dataService.getInviteLink(username);
  } catch (error) {
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const fetchConsentScripts = createAsyncThunk("data/fetchConsentScripts", async (_, { rejectWithValue }) => {
  try {
    console.log("stuff")
    return await dataService.fetchConsentScripts();
  } catch (error) {
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const addScript = createAsyncThunk("data/addScript", async (scriptData, { rejectWithValue }) => {
  try {
    const res = await dataService.addScript(scriptData);
    message.success("Script created");
    return res;
  } catch (error) {
    message.error("Failed to create script");
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const editScript = createAsyncThunk("data/editScript", async ({ script_id, updates }, { rejectWithValue }) => {
  try {
    const res = await dataService.editScript(script_id, updates);
    message.success("Script updated");
    return res;
  } catch (error) {
    message.error("Failed to update script");
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const deleteScript = createAsyncThunk("data/deleteScript", async (script_id, { rejectWithValue }) => {
  try {
    await dataService.deleteScript(script_id);
    message.success("Script deleted");
    return script_id;
  } catch (error) {
    message.error("Failed to delete script");
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const fetchFollowUps = createAsyncThunk("data/fetchFollowUps", async (_, { rejectWithValue }) => {
  try {
    return await dataService.fetchFollowUps();
  } catch (error) {
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const createFollowUp = createAsyncThunk("data/createFollowUp", async (followUpData, { rejectWithValue }) => {
  try {
    const res = await dataService.createFollowUp(followUpData);
    message.success("Follow-up created");
    return res;
  } catch (error) {
    message.error("Failed to create follow-up");
    return rejectWithValue(error.response?.data || error.message);
  }
});

export const resolveFollowUp = createAsyncThunk("data/resolveFollowUp", async (id, { rejectWithValue }) => {
  try {
    await dataService.resolveFollowUp(id);
    message.success("Follow-up resolved");
    return id;
  } catch (error) {
    message.error("Failed to resolve follow-up");
    return rejectWithValue(error.response?.data || error.message);
  }
});

// --- Slice ---
const dataSlice = createSlice({
  name: "data",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        const users = action.payload;
        state.staff = users.filter((u) => u.is_staff);
        state.participants = users.filter((u) => !u.is_staff);
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchConsentScripts.fulfilled, (state, action) => {
        state.scripts = action.payload;
      })
      .addCase(fetchFollowUps.fulfilled, (state, action) => {
        state.followUps = action.payload;
      })
      .addCase(addUser.pending, (state, action) => {
        state.loading = true;
      })
      .addCase(addUser.rejected, (state, action) => {
        state.loading = false;
      })
      .addCase(addUser.fulfilled, (state, action) => {
        state.loading = false;
        const user = action.payload.user;
        if (user.is_staff) {
          state.staff.push(user)
        } else {
          state.participants.push(user)
        }
      });
  },
});

export default dataSlice.reducer;
