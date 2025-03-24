// src/slices/authSlice.js
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { authService } from "../services/auth.service";
import { message } from "antd"; // ✅ use Ant Design's message

const storedUser = JSON.parse(localStorage.getItem("user"));

const initialState = storedUser
  ? {
      user: storedUser.user,
      accessToken: storedUser.access,
      refreshToken: storedUser.refresh,
      isAuthenticated: true,
      loading: false,
      error: null,
    }
  : {
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      loading: false,
      error: null,
    };

export const login = createAsyncThunk(
  "auth/login",
  async ({ email, password, rememberMe }, thunkAPI) => {
    try {
      const response = await authService.login({ email, password });

      message.success("Login successful! Redirecting..."); // ✅ success message

      // Store user object directly if rememberMe is enabled
      if (rememberMe) {
        localStorage.setItem("user", JSON.stringify(response));
      }

      return {
        user: response.user.user,
        accessToken: response.access,
        refreshToken: response.refresh,
        rememberMe,
      };
    } catch (error) {
      const msg =
        error?.response?.data?.detail ||
        error?.response?.data?.non_field_errors?.[0] ||
        error.message ||
        "Login failed";

      message.error(msg); // ✅ error message
      return thunkAPI.rejectWithValue({ message: msg });
    }
  }
);

export const logout = createAsyncThunk("auth/logout", async (_, thunkAPI) => {
  try {
    await authService.logout();
    message.info("Logged out successfully."); // ✅ logout info
  } catch (e) {
    message.warning("Logout error."); // optionally warn
    console.warn("Logout error", e);
  }
});

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    // --- LOGIN ---
    builder.addCase(login.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(login.fulfilled, (state, action) => {
      state.loading = false;
      console.log(JSON.stringify(action.payload))
      state.user = action.payload.user;
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
      state.isAuthenticated = true;
      state.error = null;
    });
    builder.addCase(login.rejected, (state, action) => {
      state.loading = false;
      state.isAuthenticated = false;
      state.error = action.payload?.message || "Login failed";
    });

    // --- LOGOUT ---
    builder.addCase(logout.pending, (state) => {
      state.loading = true;
    });
    builder.addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.accessToken = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.loading = false;
        state.error = null;
        localStorage.removeItem("user");
      });
    builder.addCase(logout.rejected, (state) => {
      state.loading = false;
    });
  },
});

export default authSlice.reducer;
