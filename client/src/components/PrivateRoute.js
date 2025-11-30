// src/components/PrivateRoutes.js

// src/components/PrivateRoute.js

import React, { useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { Navigate, Outlet } from "react-router-dom";
import { Spin } from "antd";
import { validateToken } from "../slices/authSlice";

const PrivateRoute = () => {
  const dispatch = useDispatch();

  const { isAuthenticated, loading, accessToken } = useSelector(
    (state) => state.auth
  );

  // Run token validation on mount
  useEffect(() => {
    if (accessToken) {
      dispatch(validateToken());
    }
  }, [dispatch, accessToken]);

  // While validating / loading → show spinner
  if (loading) {
    return (
      <div
        style={{
          width: "100%",
          height: "70vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Spin size="large" />
      </div>
    );
  }

  // After validation: if still not authenticated → redirect
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // Token is valid → render children
  return <Outlet />;
};

export default PrivateRoute;
