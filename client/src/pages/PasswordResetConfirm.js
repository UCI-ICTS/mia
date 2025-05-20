// src/pages/PasswordResetConfirm

import React, { useState } from 'react';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, message } from 'antd';
import { useDispatch } from 'react-redux';
import { activateUserAccount, confirmPasswordReset } from "../slices/authSlice";
import axios from 'axios';

const PasswordResetConfirm = () => {
  const dispatch = useDispatch();
  const [params] = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);

  const isActivation = location.pathname === "/password-create";

  const onFinish = async (values) => {
    setLoading(true);
    console.log("Component", params, isActivation, uid,token, values.new_password)
    const endpoint = isActivation ? (
        dispatch(activateUserAccount({uid,token,new_password: values.new_password}))
      ) : (
        dispatch(confirmPasswordReset({uid,token,new_password: values.new_password}))
    );
    setLoading(false);
    // navigate("/login")
  };

  return (
    <div className="login-container">
      <div className="login-form-wrapper">
        <h2>{isActivation ? "Create Your Password" : "Reset Your Password"}</h2>
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item
            name="new_password"
            label="New Password"
            rules={[{ required: true, message: "Please enter your new password" }]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item
            label="Confirm New Password"
            name="confirm_password"
            dependencies={['new_password']}
            rules={[
              { required: true, message: "Please confirm your new password" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("new_password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("Passwords do not match"));
                },
              }),
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              {isActivation ? "Create Password" : "Reset Password"}
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  );
};

export default PasswordResetConfirm;
