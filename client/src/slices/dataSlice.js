// src/slices/dataSlice.js

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { dataService } from "../services/data.service";
import { message } from "antd";

const initialState = {
  staff: [],
  participants: [],
  followUps: [],
  chat: [],
  consent: {},
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
    console.log("Slice ",userData)
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
    console.log(userId)
    await dataService.deleteUser(userId);
    message.success("User deleted successfully!");
    return userId;
  } catch (error) {
    message.error("Failed to delete user.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

//--- Invite Links ---
export const getInviteLink = createAsyncThunk(
  "data/getInviteLink",
  async (username, thunkAPI) => {
    try {
      const res = await dataService.getInviteLink(username);
      message.success("Invite link generated!");
      console.log(res)
      return res;
    } catch (error) {
      const status = error?.response?.status;
      const msg =
        status === 404
          ? "Invite link not found."
          : error.message || "Unknown error";

      return thunkAPI.rejectWithValue({ status, msg });
    }
});

export const generateInviteLink = createAsyncThunk(
  "data/generateInviteLink",
  async (username, thunkAPI) => {
    try {
      console.log("Slice invite link", username)
      const res = await dataService.generateInviteLink(username);
      message.success("Invite link generated!");
      console.log(res)
      return res;
    } catch (error) {
      const status = error?.response?.status;
      const msg =
        status === 404
          ? "Invite link not found."
          : error.message || "Unknown error";

      return thunkAPI.rejectWithValue({ status, msg });
    }
});

// --- Consent Process ---
export const fetchConsentByInvite = createAsyncThunk(
  "data/fetchConsentByInvite",
  async (invite_id, thunkAPI) => {
    try {
      const response = await dataService.getConsentByInvite(invite_id);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const submitConsentResponse = createAsyncThunk(
  "data/submitConsentResponse",
  async ({ invite_id, node_id }, thunkAPI) => {
    try {
      const response = await dataService.submitConsentResponse(invite_id, node_id);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(error?.response?.data || error.message);
    }
  }
);

export const submitConsentForm = createAsyncThunk(
  "data/submitConsentForm",
  async ({ invite_id, form_type, node_id, form_responses }, { rejectWithValue }) => {
    try {
      console.log("SLice: ", invite_id, form_type, node_id, form_responses )
      const response = await dataService.submitConsentForm({
        invite_id,
        form_type,
        node_id,
        form_responses,
      });
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);


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

export const createFollowUp = createAsyncThunk(
  "data/createFollowUp",
  async ({email, follow_up_reason, follow_up_info}, thunkAPI) => {
    try {
      console.log("Slice ", {email, follow_up_reason, follow_up_info})
      const response = await dataService.createFollowUp({email, follow_up_reason, follow_up_info});
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(error?.response?.data || error.message);
    }
  }
);

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
    console.log(scriptData)
    return await dataService.addScript(scriptData);
  } catch (error) {
    message.error("Failed to add script.");
    return thunkAPI.rejectWithValue(error.message);
  }
});

export const editScript = createAsyncThunk("data/editScript", async ({ id, ...updates }, thunkAPI) => {
  console.log(id, updates)
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

      // --- Invite ---
      .addCase(getInviteLink.pending, (state) => {
        state.loading = true;
      })
      .addCase(getInviteLink.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(getInviteLink.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.msg || "Failed to fetch invite link.";
      })

      .addCase(generateInviteLink.fulfilled, (state, action) => {
        state.loading = false;
      })
      .addCase(generateInviteLink.pending, (state, action) => {
        state.loading = true;
      })
      .addCase(generateInviteLink.rejected, (state, action) => {
        console.log(action)
        state.loading = false;
      })

      // --- Consents ---
      .addCase(fetchConsentByInvite.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchConsentByInvite.fulfilled, (state, action) => {
        if (action.payload?.chat) {
          state.chat = action.payload.chat;
        }
        state.consent = action.payload;
        state.loading = false;
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
        console.log("New chat from response:", action.payload.chat);
      
        // Replace the full chat history with updated array from backend
        if (Array.isArray(action.payload?.chat)) {
          state.chat = action.payload.chat;
        }
      
        state.loading = false;
      })      
      .addCase(submitConsentResponse.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(submitConsentForm.pending, (state) => {
        console.log("submitConsentForm.pending")
        state.loading = true;
        state.error = null;
      })
      .addCase(submitConsentForm.fulfilled, (state, action) => {
        console.log("submitConsentForm.fulfilled", action.payload)
        state.loading = false;
        if (Array.isArray(action.payload?.chat)) {
          state.chat = action.payload.chat;
        }
        state.error = null;
        message.success("Form submitted!");
      })
      .addCase(submitConsentForm.rejected, (state, action) => {
        console.log("submitConsentForm.rejected", action.payload)
        state.loading = false;
        state.error = action.payload.error || "Form submission failed";
        message.error(state.error);
      })

    // --- FOLLOW UPS ---
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
      })
      .addCase(createFollowUp.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createFollowUp.fulfilled, (state, action) => {
        state.loading = false;
        message.success("Message sent!");
      })
      .addCase(createFollowUp.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      
        let errorMsg = "Something went wrong.";
        const payload = action.payload;
      
        if (typeof payload === "string") {
          errorMsg = payload;
        } else if (typeof payload === "object" && payload !== null) {
          // Combine all key-value pairs into readable messages
          errorMsg = Object.entries(payload)
            .map(([field, messages]) => {
              const msgText = Array.isArray(messages) ? messages.join(", ") : messages;
              return `${field}: ${msgText}`;
            })
            .join("\n");
        }
      
        message.error(errorMsg);
      })      

    // --- SCRIPTS ---
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
      });
  },
});

export default dataSlice.reducer;
