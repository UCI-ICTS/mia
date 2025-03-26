// src/components.FollowUpModal.js

import React from "react";
import { Modal, Form, Input, Select, Button, message } from "antd";

const { TextArea } = Input;
const { Option } = Select;

const FollowUpFormModal = ({ visible, onClose, onSubmit, userInfo = {} }) => {
  const [form] = Form.useForm();

  const handleFinish = async (values) => {
    try {
      await onSubmit(values);
      message.success("Your message has been sent!");
      form.resetFields();
      onClose();
    } catch (err) {
      message.error("Failed to submit follow-up.");
    }
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
