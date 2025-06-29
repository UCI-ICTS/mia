import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";
import dataReducer from "./slices/dataSlice";
import consentReducer from "./slices/consentSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    data: dataReducer,
    consentChat: consentReducer,
  },
});
