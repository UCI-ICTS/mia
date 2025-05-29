// src/components.FollowUpModal.js

import React from "react";
import { Modal, Form, Input, Select, Button } from "antd";
import { useDispatch, useSelector } from "react-redux";
import { createFollowUp } from "../slices/dataSlice";

const { TextArea } = Input;
const { Option } = Select;

const FollowUpFormModal = ({ visible, onClose, userInfo = {} }) => {
  const dispatch = useDispatch();
  const { chat = [], consent, loading, error } = useSelector((state) => state.consentChat);
  const [form] = Form.useForm();
  const lastMessage = chat[chat.length - 1]?.node_id;
  
  const handleFinish = (values) => {
    const updatedMoreInfo = `${values.more_info || ""}\n\nLast Node ID: ${lastMessage}`;
    dispatch(createFollowUp({
        "email": values.email,
        "follow_up_reason": values.reason,
        "follow_up_info": updatedMoreInfo
      }))
    form.resetFields();
    onClose();
  };
  
  return (
    <Modal
      title="Contact the Study Team"
      open={visible}
      onCancel={onClose}
      footer={null}
    >
      <Form
        layout="vertical"
        form={form}
        initialValues={{
          first_name: userInfo.first_name || "",
          last_name: userInfo.last_name || "",
          email: userInfo.email || "",
          phone: userInfo.phone || "",
          reason: "question",
        }}
        onFinish={handleFinish}
      >
        <Form.Item name="first_name" label="First Name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="last_name" label="Last Name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="email" label="Email" rules={[{ required: true, type: "email" }]}>
          <Input />
        </Form.Item>
        <Form.Item name="phone" label="Phone">
          <Input />
        </Form.Item>
        <Form.Item name="reason" label="Reason for Contact" rules={[{ required: true }]}>
          <Select>
            <Option value="question">I have a question</Option>
            <Option value="technical">I need technical help</Option>
            <Option value="privacy">I have privacy concerns</Option>
            <Option value="other">Other</Option>
          </Select>
        </Form.Item>
        <Form.Item name="more_info" label="More Info">
          <TextArea rows={4} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">
            Submit Request
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default FollowUpFormModal;
