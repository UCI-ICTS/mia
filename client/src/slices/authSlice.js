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
    message.info("Logged out successfully.");
  } catch (e) {
    message.warning("Logout error.");
    console.warn("Logout error", e);
  }
});

export const resetPassword = createAsyncThunk(
  "auth/reset_password",
  async (email, thunkAPI) => {
    try {
      console.log("Slice password reset: ", email);
      const response = await authService.resetPassword(email);
      console.log(response.message)
      message.success(response.message)
      return response.data;
    } catch (error) {
      console.log("Slice password reset error: ", error);

      let errorMessage = "An error occurred";

      if (error.response) {
        const errorData = error.response.data;

        if (typeof errorData === "string") {
          // If backend just returns a plain error message
          errorMessage = errorData;
        } else if (errorData?.detail) {
          errorMessage = errorData.detail;
        } else if (typeof errorData === "object") {
          errorMessage = Object.entries(errorData)
            .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(", ") : errors}`)
            .join(" | ");
        } else {
          errorMessage = `Request failed with status ${error.response.status}`;
        }

      } else if (error.message) {
        errorMessage = error.message;
      }

      message.error(errorMessage);
      return thunkAPI.rejectWithValue(errorMessage);
    }
  }
);

export const confirmPasswordReset = createAsyncThunk(
  "auth/confirm_password_reset",
  async ({ uid, token, new_password }, thunkAPI) => {
    try {
      const response = await authService.confirmPasswordReset({ uid, token, new_password });
      message.success("Password reset successful")
      return response.data;
    } catch (error) {
      console.log("Slice confirm reset error:", error);

      let errorMessage = "An error occurred";

      if (error.response) {
        const errorData = error.response.data;

        if (typeof errorData === "string") {
          errorMessage = errorData;
        } else if (errorData?.detail) {
          errorMessage = errorData.detail;
        } else if (typeof errorData === "object") {
          errorMessage = Object.entries(errorData)
            .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(", ") : errors}`)
            .join(" | ");
        } else {
          errorMessage = `Request failed with status ${error.response.status}`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      message.error(errorMessage);
      return thunkAPI.rejectWithValue(errorMessage);
    }
  }
);

export const activateUserAccount = createAsyncThunk(
  "auth/activate_account",
  async ({ uid, token, new_password }, thunkAPI) => {
    try {
      const response = await authService.createPassword({ uid, token, new_password });
      return response.data;
    } catch (error) {
      console.log("Slice activation error:", error);

      let errorMessage = "An error occurred";

      if (error.response) {
        const errorData = error.response.data;

        if (typeof errorData === "string") {
          errorMessage = errorData;
        } else if (errorData?.detail) {
          errorMessage = errorData.detail;
        } else if (typeof errorData === "object") {
          errorMessage = Object.entries(errorData)
            .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(", ") : errors}`)
            .join(" | ");
        } else {
          errorMessage = `Request failed with status ${error.response.status}`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      message.error(errorMessage);
      return thunkAPI.rejectWithValue(errorMessage);
    }
  }
);

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

    // --- Submit Password Reset ---
    builder.addCase(resetPassword.pending, (state) => {
      state.loading = true;
      state.error = null;
    })
    builder.addCase(resetPassword.fulfilled, (state, action) => {
      state.loading = false;
    })
    builder.addCase(resetPassword.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload;
    })

    // --- Confirm Password Reset ---
    builder.addCase(confirmPasswordReset.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(confirmPasswordReset.fulfilled, (state, action) => {
      state.loading = false;
    });
    builder.addCase(confirmPasswordReset.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload;
    });

    // --- Activate Account ---
    builder.addCase(activateUserAccount.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(activateUserAccount.fulfilled, (state, action) => {
      state.loading = false;
    });
    builder.addCase(activateUserAccount.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload;
    });
  },
});

export default authSlice.reducer;
