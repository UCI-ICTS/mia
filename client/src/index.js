// src/index.js

import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import { store } from "./store";
import AppRoutes from "./routes";
import { ConfigProvider } from "antd"; // Ant Design v5 support

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <Provider store={store}>
    <ConfigProvider>
      <AppRoutes />
    </ConfigProvider>
  </Provider>
);
