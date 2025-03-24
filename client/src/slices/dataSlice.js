// src/slices/dataSlice.js

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { dataService } from "../services/data.service";
import { message } from "antd";

const initialState = {
  staff: [],
  participants: [],
  followUps: [],
  scripts: [],
  loading: false,
  error: null,
};

// --- Users ---

export const fetchUsers = createAsyncThunk("data/fetchUsers", async (_, thunkAPI) => {
  try {
    return await dataService.getUsers();
  } catch (error) {
    message.error("Failed to fetch users.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const addUser = createAsyncThunk("data/addUser", async (userData, thunkAPI) => {
  try {
    const res = await dataService.createUser(userData);
    message.success("User added successfully!");
    return res;
  } catch (error) {
    console.log(error)
    let errorMessage = "Login failed. Please try again."; // Default message
    message.error("Failed to add participant. A participant with that email probably exists");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const updateUser = createAsyncThunk("data/updateUser", async (userData, thunkAPI) => {
  try {
    const res = await dataService.updateUser(userData);
    message.success("User updated successfully!");
    return res;
  } catch (error) {
    message.error("Failed to update user.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const deleteUser = createAsyncThunk("data/deleteUser", async (userId, thunkAPI) => {
  try {
    await dataService.deleteUser(userId);
    message.success("User deleted successfully!");
    return userId;
  } catch (error) {
    message.error("Failed to delete user.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const getInviteLink = createAsyncThunk("data/getInviteLink", async (userId, thunkAPI) => {
  try {
    const res = await dataService.getInviteLink(userId);
    message.success("Invite link generated!");
    return res;
  } catch (error) {
    message.error("Failed to generate invite link.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

// --- Follow Ups ---

export const fetchFollowUps = createAsyncThunk("data/fetchFollowUps", async (_, thunkAPI) => {
  try {
    return await dataService.getFollowUps();
  } catch (error) {
    message.error("Failed to fetch follow-ups.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const resolveFollowUp = createAsyncThunk("data/resolveFollowUp", async (id, thunkAPI) => {
  try {
    await dataService.markFollowUpResolved(id);
    message.success("Follow-up marked as resolved!");
    return id;
  } catch (error) {
    message.error("Failed to resolve follow-up.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

// --- Scripts ---

export const fetchScripts = createAsyncThunk("data/fetchScripts", async (_, thunkAPI) => {
  try {
    return await dataService.getScripts();
  } catch (error) {
    message.error("Failed to fetch scripts.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const addScript = createAsyncThunk("data/addScript", async (scriptData, thunkAPI) => {
  try {
    return await dataService.addScript(scriptData);
  } catch (error) {
    message.error("Failed to add script.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const editScript = createAsyncThunk("data/editScript", async ({ id, ...updates }, thunkAPI) => {
  try {
    return await dataService.editScript(id, updates);
  } catch (error) {
    message.error("Failed to edit script.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const deleteScript = createAsyncThunk("data/deleteScript", async (id, thunkAPI) => {
  try {
    await dataService.deleteScript(id);
    return id;
  } catch (error) {
    message.error("Failed to delete script.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

const dataSlice = createSlice({
  name: "data",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    // --- USERS ---
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

      .addCase(addUser.fulfilled, (state, action) => {
        const user = action.payload;
        if (user.is_staff) {
          state.staff.push(user);
        } else {
          state.participants.push(user);
        }
      })

      .addCase(updateUser.fulfilled, (state, action) => {
        const updated = action.payload;
        const list = updated.is_staff ? "staff" : "participants";
        state[list] = state[list].map((u) =>
          u.id === updated.id ? updated : u
        );
      })

      .addCase(deleteUser.fulfilled, (state, action) => {
        const id = action.payload;
        state.staff = state.staff.filter((u) => u.id !== id);
        state.participants = state.participants.filter((u) => u.id !== id);
      })

      .addCase(getInviteLink.pending, (state) => {
        state.loading = true;
      })
      .addCase(getInviteLink.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(getInviteLink.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });

    // --- FOLLOW UPS ---
    builder
      .addCase(fetchFollowUps.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFollowUps.fulfilled, (state, action) => {
        state.loading = false;
        state.followUps = action.payload;
      })
      .addCase(fetchFollowUps.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(resolveFollowUp.fulfilled, (state, action) => {
        const id = action.payload;
        state.followUps = state.followUps.map((f) =>
          f.user_follow_up_id === id ? { ...f, resolved: true } : f
        );
      });

    // --- SCRIPTS ---
    builder
      .addCase(fetchScripts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchScripts.fulfilled, (state, action) => {
        state.loading = false;
        state.scripts = action.payload;
      })
      .addCase(fetchScripts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(addScript.fulfilled, (state, action) => {
        state.scripts.push(action.payload);
      })
      .addCase(editScript.fulfilled, (state, action) => {
        state.scripts = state.scripts.map((s) =>
          s.consent_id === action.payload.consent_id ? action.payload : s
        );
      })
      .addCase(deleteScript.fulfilled, (state, action) => {
        state.scripts = state.scripts.filter((s) => s.chat_id !== action.payload);
      });
  },
});

export default dataSlice.reducer;
