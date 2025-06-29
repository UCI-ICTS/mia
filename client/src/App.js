// src/App.js

import { useEffect } from "react";
import { message } from "antd";
import AppRoutes from "./routes";
import PageTitleManager from "./components/PageTitleManager";

function App() {
  useEffect(() => {
    message.config({ top: 80, duration: 5 });
  }, []);

  return (<AppRoutes />);
}

export default App;
