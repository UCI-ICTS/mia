// src/components/PageTitleManager.js
import { useLocation } from "react-router-dom";
import { useEffect } from "react";

const titleMap = {
  "/login": "Login",
  "/dashboard": "Dashboard",
  "/password-reset": "Reset Password",
  "/password-create": "Create Password",
  "/consent/:session_slug": "Consent Chat",
  // Add more routes as needed
};

function getTitleFromPath(pathname) {
  // Match dynamic routes
  if (pathname.startsWith("/consent/")) return "Consent Chat";

  // Exact matches
  return titleMap[pathname] || "Medical Information Assistant (MIA)";
}

const PageTitleManager = () => {
  const location = useLocation();

  useEffect(() => {
    const title = getTitleFromPath(location.pathname);
    document.title = `${title} | MIA`;
  }, [location.pathname]);

  return null;
};

export default PageTitleManager;
