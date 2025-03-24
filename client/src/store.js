import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";
import dataReducer from "./slices/dataSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    data: dataReducer,
  },
});
