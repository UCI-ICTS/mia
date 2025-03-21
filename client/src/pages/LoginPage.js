// src/pages/LoginPage.js

import { Checkbox, Form, Input, Button, Typography, Card, message } from "antd";
import { useDispatch, useSelector } from "react-redux";
import { login } from "../slices/authSlice";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const { Title } = Typography;

const LoginPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate(); 
  const { error, isAuthenticated } = useSelector((state) => state.auth);
  const [rememberMe, setRememberMe] = useState(false);
  
  const onFinish = (values) => {
    dispatch(login({ email: values.email, password: values.password, rememberMe }));
  };

  useEffect(() => {
    if (isAuthenticated) {
      message.success("Login successful! Redirecting...");
      navigate("/dashboard", { replace: true }); // Redirect to admin dashboard
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (error) {
      message.error(error.message || "Login failed. Please try again.");
    }
  }, [error]);

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
      <Card style={{ width: 350, padding: "20px" }}>
        <Title level={3} style={{ textAlign: "center" }}>Login</Title>
        <Form name="loginForm" onFinish={onFinish} layout="vertical">
          <Form.Item 
            label="Email" 
            name="email" 
            rules={[{ required: true, type: "email", message: "Please enter a valid email" }]}
          >
            <Input placeholder="Enter your email" />
          </Form.Item>
          <Form.Item 
            label="Password" 
            name="password" 
            rules={[{ required: true, message: "Please enter your password" }]}
          >
            <Input.Password placeholder="Enter your password" />
          </Form.Item>
          <Form.Item>
            <Checkbox checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)}>
              Remember Me
            </Checkbox>
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            Login
          </Button>
        </Form>
      </Card>
    </div>
  );
};

export default LoginPage;
