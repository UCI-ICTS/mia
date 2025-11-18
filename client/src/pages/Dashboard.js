// src/pages/Dashboard.js

import "../style.css";
import { useEffect, useState } from "react";
import { Layout, Menu, Button } from "antd";
import { HomeOutlined, UserOutlined, ScheduleOutlined, MessageOutlined, TeamOutlined, LogoutOutlined, PaperClipOutlined } from "@ant-design/icons";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { logout } from "../slices/authSlice";
import { fetchUsers, fetchFollowUps, fetchConsentScripts } from "../slices/dataSlice"
import { useLocation } from "react-router-dom";

const { Sider, Content } = Layout;

const Dashboard = () => {
  const location = useLocation();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const {staff,participants,loading,error} = useSelector((state) => state.data || {});
  
  useEffect(() => {
    if (!loading && !error && (!staff || staff.length === 0)) {
      dispatch(fetchUsers());
      dispatch(fetchFollowUps());
      dispatch(fetchConsentScripts());
    }
  }, [participants, loading, error, dispatch, staff]);

  const handleLogout = () => {
    dispatch(logout());
    navigate("/"); // redirect to login
  };

  const menuItems = [
    {key: "home", icon: <HomeOutlined/>, label: <Link to="/dashboard">Summary Console</Link>},
    {key: "participants", icon: <UserOutlined/>, label: <Link to="/dashboard/participants">Participants</Link>},
    {key: "follow-up", icon: <ScheduleOutlined/>, label: <Link to="/dashboard/follow_up">Participant Follow Up</Link>},
    {key: "docs", icon: <PaperClipOutlined />, label: <Link to="/dashboard/documents">Participant Documents</Link>},
    {key: "scripts", icon: <MessageOutlined/>, label: <Link to="/dashboard/scripts">Consentbot Scripts</Link>},
    {key: "admin", icon: <TeamOutlined/>, label: <Link to="/dashboard/admin">Manage Staff & Admin </Link>},
  ];
  
  const getActiveMenuKey = (pathname) => {
    if (pathname.startsWith("/dashboard/participants")) return "participants";
    if (pathname.startsWith("/dashboard/follow_up")) return "follow-up";
    if (pathname.startsWith("/dashboard/documents")) return "docs";
    if (pathname.startsWith("/dashboard/scripts")) return "scripts";
    if (pathname.startsWith("/dashboard/admin")) return "admin";
    return "home";
  };

  const activeKey = getActiveMenuKey(location.pathname);
  
  return (
    <Layout className="layout">
      {/* Sidebar */}
      <Sider
        width={250}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        className="sider-container"
      >
        <h2 className="sider-header">{collapsed ? "" : "Kauro Admin Dashboard"}</h2>
        <div className="sider-menu-wrapper">
          <Menu
            theme="dark"
            mode="inline"
            defaultSelectedKeys={[activeKey]}
            style={{ borderRight: 0 }}
            items={menuItems}
          />
        </div>
        {/* User Info and Logout */}
        <div className="logout-button-container">  
          <Button
            className="logout-button"
            icon={<LogoutOutlined/>}
            style={{ width: "80%", marginTop: "5px" }} 
            onClick={handleLogout}
          >{!collapsed && "Logout"}</Button>
        </div>
      </Sider>

      {/* Content Area */}
      <Layout className="layout-dashboard">
        <Content>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;
