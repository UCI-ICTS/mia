// src/App.js

import AppRoutes from "./routes";
import { message } from "antd";

function App() {
  {message.config({ top: 80, duration: 2 })} {/* Ensure messages are visible */}
  return <AppRoutes />;
}

export default App;
