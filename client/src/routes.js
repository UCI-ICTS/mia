// src/routes.js

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import ConsentPage from "./pages/ConsentPage";
import PasswordResetConfirm from "./pages/PasswordResetConfirm";
import AdminConsole from "./components/AdminConsole";
import ManageParticipants from "./components/ManageParticipants";
import FollowUp from "./components/FollowUp";
import ConsentScripts from "./components/ConsentScripts";
import ManageAdministrators from "./components/ManageAdministrators";
import PrivateRoute from "./components/PrivateRoute";
import ViewScriptContent from "./components/ViewScriptContent";
import EditScriptContent from "./components/EditScriptContent";

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/consent/:invite_id" element={<ConsentPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/password-reset" element={<PasswordResetConfirm />} />
        <Route path="/password-create" element={<PasswordResetConfirm />} />

        {/* Protected Admin Dashboard */}
        <Route element={<PrivateRoute />}>
          <Route path="/dashboard" element={<Dashboard />}>
            <Route index element={<AdminConsole />} />
            <Route path="participants" element={<ManageParticipants/>} />
            <Route path="follow_up" element={<FollowUp />} />
            <Route path="scripts" element={<ConsentScripts />} />
            <Route path="scripts/view/:script_id" element={<ViewScriptContent />} />
            <Route path="scripts/edit/:script_id" element={<EditScriptContent />} />
            <Route path="admin" element={<ManageAdministrators />} />
          </Route>
        </Route>
      </Routes>
    </Router>
  );
};

export default AppRoutes;
