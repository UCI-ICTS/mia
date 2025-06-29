// src/pages/LoginPage.js

import { Checkbox, Form, Input, Button, Typography, Modal, Card, message } from "antd";
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
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              Login
            </Button>
          </Form.Item>
          <Form.Item>
            <Button
              onClick={showModal}
            >Forgot Password</Button>
          </Form.Item>
        </Form>
      </Card>
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
