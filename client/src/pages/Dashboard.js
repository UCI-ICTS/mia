// src/pages/Dashboard.js

import { Layout, Menu, Button, Typography } from "antd";
import { HomeOutlined, UserOutlined, ScheduleOutlined, MessageOutlined, TeamOutlined } from "@ant-design/icons";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { logout } from "../slices/authSlice";
const { Sider, Content } = Layout;
const { Title } = Typography;

const Dashboard = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const user = useSelector((state) => state.auth.user);

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login"); // redirect to login
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {/* Sidebar */}
      <Sider width={240} style={{ background: "#f5f5f5", padding: "20px" }}>
        <Title level={4} style={{ textAlign: "center" }}>Admin</Title>
        <Menu mode="vertical" defaultSelectedKeys={["home"]} style={{ borderRight: 0 }}>
          <Menu.Item key="home" icon={<HomeOutlined />}>
            <Link to="/dashboard/home">Home</Link>
          </Menu.Item>
          <Menu.Item key="users" icon={<UserOutlined />}>
            <Link to="/dashboard/users">Participants</Link>
          </Menu.Item>
          <Menu.Item key="follow-up" icon={<ScheduleOutlined />}>
            <Link to="/dashboard/follow_up">Participant Follow Up</Link>
          </Menu.Item>
          <Menu.Item key="scripts" icon={<MessageOutlined />}>
            <Link to="/dashboard/scripts">Chatbot Scripts</Link>
          </Menu.Item>
          <Menu.Item key="members" icon={<TeamOutlined />}>
            <Link to="/dashboard/members">Manage Admin Users</Link>
          </Menu.Item>
        </Menu>

        {/* User Info and Logout */}
        <div style={{ position: "absolute", bottom: 20, width: "100%", textAlign: "center", padding: "0 10px" }}>
          <Button type="text" block style={{ width: "80%", marginTop: "5px" }} >
            {user?.first_name} {user?.last_name}
          </Button>
          <Button 
            danger 
            style={{ width: "80%", marginTop: "5px" }} 
            onClick={handleLogout}
          >
  Logout
</Button>

        </div>

      </Sider>

      {/* Content Area */}
      <Layout style={{ padding: "20px", background: "#fff" }}>
        <Content>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;
