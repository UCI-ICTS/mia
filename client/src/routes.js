// src/routes.js

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import AdminConsole from "./components/AdminConsole";
import ManageParticipants from "./components/ManageParticipants";
import FollowUp from "./components/FollowUp";
import ConsentScripts from "./components/ConsentScripts";
import ManageAdministrators from "./components/ManageAdministrators";
import PrivateRoute from "./components/PrivateRoute"; // Import PrivateRoute

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Admin Dashboard */}
        <Route element={<PrivateRoute />}>
          <Route path="/dashboard" element={<Dashboard />}>
            <Route path="home" element={<AdminConsole />} />
            <Route path="users" element={<ManageParticipants/>} />
            <Route path="follow_up" element={<FollowUp />} />
            <Route path="scripts" element={<ConsentScripts />} />
            <Route path="members" element={<ManageAdministrators />} />
          </Route>
        </Route>
      </Routes>
    </Router>
  );
};

export default AppRoutes;
