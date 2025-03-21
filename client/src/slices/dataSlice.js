// src/slices/dataSlice.js

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { dataService } from "../services/data.service";
import { message } from "antd";

const initialState = {
  users: [],
  followUps: [],
  scripts: [],
  loading: false,
  error: null,
};

// ✅ Fetch Scripts
export const fetchScripts = createAsyncThunk(
    "data/fetchScripts",
    async (_, thunkAPI) => {
      try {
        const response = await dataService.getScripts();
        return response;
      } catch (error) {
        message.error("Failed to fetch scripts.");
        return thunkAPI.rejectWithValue(error.message);
      }
    }
  );
  
  // ✅ Add Script
  export const addScript = createAsyncThunk(
    "data/addScript",
    async (scriptData, thunkAPI) => {
      try {
        const response = await dataService.addScript(scriptData);
        return response;
      } catch (error) {
        message.error("Failed to add script.");
        return thunkAPI.rejectWithValue(error.message);
      }
    }
  );
  
  // ✅ Edit Script
  export const editScript = createAsyncThunk(
    "data/editScript",
    async ({ id, ...updates }, thunkAPI) => {
      try {
        const response = await dataService.editScript(id, updates);
        return response;
      } catch (error) {
        message.error("Failed to edit script.");
        return thunkAPI.rejectWithValue(error.message);
      }
    }
  );
  
  // ✅ Delete Script
  export const deleteScript = createAsyncThunk(
    "data/deleteScript",
    async (id, thunkAPI) => {
      try {
        await dataService.deleteScript(id);
        return id;
      } catch (error) {
        message.error("Failed to delete script.");
        return thunkAPI.rejectWithValue(error.message);
      }
    }
  );
  
// ✅ Fetch Follow-Ups
export const fetchFollowUps = createAsyncThunk(
    "data/fetchFollowUps",
    async (_, thunkAPI) => {
      try {
        const response = await dataService.getFollowUps();
        return response;
      } catch (error) {
        message.error("Failed to fetch follow-ups.");
        return thunkAPI.rejectWithValue(error.message);
      }
    }
  );
  
  // ✅ Resolve Follow-Up
  export const resolveFollowUp = createAsyncThunk(
    "data/resolveFollowUp",
    async (id, thunkAPI) => {
      try {
        await dataService.markFollowUpResolved(id);
        message.success("Follow-up marked as resolved!");
        return id;
      } catch (error) {
        message.error("Failed to resolve follow-up.");
        return thunkAPI.rejectWithValue(error.message);
      }
    }
  );

// ✅ Fetch Users
export const fetchUsers = createAsyncThunk(
  "data/fetchUsers",
  async (_, thunkAPI) => {
    try {
      const response = await dataService.getUsers();
      return response;
    } catch (error) {
      message.error(error.message || "Failed to fetch users.");
      return thunkAPI.rejectWithValue(error.message);
    }
  }
);

// ✅ Add User
export const addUser = createAsyncThunk(
  "data/addUser",
  async (userData, thunkAPI) => {
    try {
      const response = await dataService.createUser(userData);
      message.success("User added successfully!");
      return response;
    } catch (error) {
      message.error(error.message || "Failed to add user.");
      return thunkAPI.rejectWithValue(error.message);
    }
  }
);

// ✅ Update User
export const updateUser = createAsyncThunk(
  "data/updateUser",
  async (userData, thunkAPI) => {
    try {
      const response = await dataService.updateUser(userData);
      message.success("User updated successfully!");
      return response;
    } catch (error) {
      message.error(error.message || "Failed to update user.");
      return thunkAPI.rejectWithValue(error.message);
    }
  }
);

// ✅ Delete User
export const deleteUser = createAsyncThunk(
  "data/deleteUser",
  async (userId, thunkAPI) => {
    try {
      await dataService.deleteUser(userId);
      message.success("User deleted successfully!");
      return userId;
    } catch (error) {
      message.error(error.message || "Failed to delete user.");
      return thunkAPI.rejectWithValue(error.message);
    }
  }
);

// ✅ Get Invite Link
export const getInviteLink = createAsyncThunk(
  "data/getInviteLink",
  async (userId, thunkAPI) => {
    try {
      const response = await dataService.getInviteLink(userId);
      message.success("Invite link generated!");
      return response;
    } catch (error) {
      message.error(error.message || "Failed to generate invite link.");
      return thunkAPI.rejectWithValue(error.message);
    }
  }
);

// --- Admin Members ---
export const fetchMembers = createAsyncThunk("data/fetchMembers", async (_, thunkAPI) => {
    try {
      return await dataService.getMembers();
    } catch (err) {
      return thunkAPI.rejectWithValue(err.message);
    }
  });
  
  export const addMember = createAsyncThunk("data/addMember", async (memberData, thunkAPI) => {
    try {
      return await dataService.addMember(memberData);
    } catch (err) {
      return thunkAPI.rejectWithValue(err.message);
    }
  });
  
  export const editMember = createAsyncThunk("data/editMember", async ({ id, ...updates }, thunkAPI) => {
    try {
      return await dataService.editMember(id, updates);
    } catch (err) {
      return thunkAPI.rejectWithValue(err.message);
    }
  });
  
  export const deleteMember = createAsyncThunk("data/deleteMember", async (id, thunkAPI) => {
    try {
      await dataService.deleteMember(id);
      return id;
    } catch (err) {
      return thunkAPI.rejectWithValue(err.message);
    }
  });

const dataSlice = createSlice({
  name: "data",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      // ✅ Fetch Users
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.users = action.payload;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // ✅ Add User
      .addCase(addUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(addUser.fulfilled, (state, action) => {
        state.loading = false;
        state.users.push(action.payload);
      })
      .addCase(addUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // ✅ Update User
      .addCase(updateUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(updateUser.fulfilled, (state, action) => {
        state.loading = false;
        state.users = state.users.map((user) =>
          user.user_id === action.payload.user_id ? action.payload : user
        );
      })
      .addCase(updateUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // ✅ Delete User
      .addCase(deleteUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(deleteUser.fulfilled, (state, action) => {
        state.loading = false;
        state.users = state.users.filter((user) => user.user_id !== action.payload);
      })
      .addCase(deleteUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // ✅ Get Invite Link
      .addCase(getInviteLink.pending, (state) => {
        state.loading = true;
      })
      .addCase(getInviteLink.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(getInviteLink.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // ✅ Fetch Follow-Ups
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

      // ✅ Resolve Follow-Up
      .addCase(resolveFollowUp.fulfilled, (state, action) => {
        state.followUps = state.followUps.map((followUp) =>
          followUp.user_follow_up_id === action.payload ? { ...followUp, resolved: true } : followUp
        );
      })
      // ✅ Fetch Scripts
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

      // ✅ Add Script
      .addCase(addScript.fulfilled, (state, action) => {
        state.scripts.push(action.payload);
      })

      // ✅ Edit Script
      .addCase(editScript.fulfilled, (state, action) => {
        state.scripts = state.scripts.map((script) =>
          script.chat_id === action.payload.chat_id ? action.payload : script
        );
      })

      // ✅ Delete Script
      .addCase(deleteScript.fulfilled, (state, action) => {
        state.scripts = state.scripts.filter((script) => script.chat_id !== action.payload);
      })

      .addCase(fetchMembers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })

      .addCase(fetchMembers.fulfilled, (state, action) => {
        state.loading = false;
        state.members = action.payload;
      })

      .addCase(fetchMembers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      .addCase(addMember.fulfilled, (state, action) => {
        state.members.push(action.payload);
      })

      .addCase(editMember.fulfilled, (state, action) => {
        state.members = state.members.map((m) =>
          m.member_id === action.payload.member_id ? action.payload : m
        );
      })
      
      .addCase(deleteMember.fulfilled, (state, action) => {
        state.members = state.members.filter((m) => m.member_id !== action.payload);
      });
  },
});

export default dataSlice.reducer;
