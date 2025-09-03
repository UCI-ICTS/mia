// src/pages/LoginPage.js

import "../style.css";
import { Checkbox, Form, Input, Button, Typography, Modal, Card, message } from "antd";
import { MailOutlined, LockOutlined } from "@ant-design/icons";
import { useDispatch, useSelector } from "react-redux";
import { login, resetPassword } from "../slices/authSlice";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const { Title } = Typography;

const LoginPage = () => {
  const [form] = Form.useForm();
  const dispatch = useDispatch();
  const navigate = useNavigate(); 
  const { error, isAuthenticated } = useSelector((state) => state.auth);
  const [passwordResetModal, setPasswordResetModal] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  
  const showModal = () => {
    setPasswordResetModal(true);
  };

  const submitReset = (values) => {
    dispatch(resetPassword(values.email))
    form.resetFields();
    setPasswordResetModal(false);
  };

  const handleCancel = () => {
    form.resetFields();
    setPasswordResetModal(false);
  };

  const onFinish = (values) => {
    dispatch(login({ email: values.email, password: values.password, rememberMe }));
  };

  useEffect(() => {
    if (isAuthenticated) {
      message.success("Login successful! Redirecting...");
      navigate("/dashboard", { replace: true }); // Redirect to admin dashboard
    }
  }, [isAuthenticated, navigate]);


  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-form-wrapper">
          <h2>MIA Staff Login</h2>
          <Form name="loginForm" onFinish={onFinish} className="login-form">
            <Form.Item 
              label="Email" 
              name="email" 
              rules={[{ required: true, type: "email", message: "Please enter a valid email" }]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="Enter your email" 
                autoComplete="email"
              />
            </Form.Item>
            <Form.Item 
              label="Password" 
              name="password" 
              rules={[{ required: true, message: "Please enter your password" }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                type="password"
                placeholder="Enter your password"
                autoComplete="current-password"
              />
            </Form.Item>
            <Form.Item>
              <Checkbox checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)}>
                Remember Me
              </Checkbox>
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" className="login-form-button">
                Login
              </Button>
            </Form.Item>
            <Form.Item>
              <Button
                onClick={showModal}
              >Forgot Password</Button>
            </Form.Item>
          </Form>
        </div>
      </div>
      <Modal
        title="Password reset"
        open={passwordResetModal}
        onCancel={handleCancel}
        footer={null}
        width={500}
      >
        <Form layout="vertical" onFinish={submitReset}>
          <Form.Item
            name="email"
            label="Email"
            rules={[{ required: true, message: "Please enter a valid email" }]}
          >
            <Input type="email" autoComplete="email" />
          </Form.Item>
          <Form.Item>
            <Button onClick={handleCancel} style={{ marginRight: 8 }}>
              Cancel
            </Button>
            <Button type="primary" htmlType="submit">
              Submit
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default LoginPage;
