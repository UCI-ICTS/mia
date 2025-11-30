// src/routes.js

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import LoginPage from "./pages/LoginPage";
import ConsentPage from "./pages/ConsentPage";
import SummaryConsole from "./pages/SummaryConsole";
import PasswordResetConfirm from "./pages/PasswordResetConfirm";
import ManageParticipants from "./pages/ManageParticipants";
import ManageAdministrators from "./pages/ManageAdministrators";
import FollowUp from "./pages/FollowUp";
import ConsentScripts from "./pages/ConsentScripts";
import GraphPage from "./pages/GraphPage";
import DocumentsPage from "./pages/DocumentsPage";
import PrivateRoute from "./components/PrivateRoute";

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/consent/:session_slug" element={<ConsentPage />} />
        <Route path="/password-reset" element={<PasswordResetConfirm />} />
        <Route path="/password-create" element={<PasswordResetConfirm />} />

        {/* Protected Admin Dashboard */}
        <Route element={<PrivateRoute />}>
          <Route path="/dashboard" element={<Dashboard />}>
            <Route index element={<SummaryConsole />} />
            <Route path="participants" element={<ManageParticipants/>} />
            <Route path="follow_up" element={<FollowUp />} />
            <Route path="scripts" element={<ConsentScripts />} />
            <Route path="scripts/view/:script_id" element={<GraphPage />} />
            <Route path="admin" element={<ManageAdministrators />} />
            <Route path="documents" element={<DocumentsPage />} />
          </Route>
        </Route>
      </Routes>
    </Router>
  );
};

export default AppRoutes;
