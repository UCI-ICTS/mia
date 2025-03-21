// src/components/ManageAdministrators.js

import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchMembers,
  addMember,
  editMember,
  deleteMember,
} from "../slices/dataSlice";
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Spin,
  Alert,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import ErrorBoundary from "./ErrorBoundary";

const { Option } = Select;

const ManageAdministrators = () => {
  const dispatch = useDispatch();
  const { members = [], loading, error } = useSelector(
    (state) => state.data || {}
  );

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingMember, setEditingMember] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    dispatch(fetchMembers()).catch(() =>
      message.error("Failed to load members")
    );
  }, [dispatch]);

  const handleOpenModal = (member = null) => {
    setEditingMember(member);
    form.setFieldsValue({
      full_name: member?.full_name || "",
      email: member?.email || "",
      password: "", // Don't preload password
      role: member?.role || undefined,
    });
    setIsModalVisible(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingMember) {
      await dispatch(editMember({ id: editingMember.member_id, ...values }));
      message.success("Member updated.");
    } else {
      await dispatch(addMember(values));
      message.success("Member added.");
    }
    setIsModalVisible(false);
    dispatch(fetchMembers());
  };

  const handleDelete = async (id) => {
    await dispatch(deleteMember(id));
    message.success("Member deleted.");
    dispatch(fetchMembers());
  };

  const columns = [
    { title: "Name", dataIndex: "full_name" },
    { title: "Email", dataIndex: "email" },
    { title: "Role", dataIndex: "role" },
    { title: "Created", dataIndex: "created_at" },
    {
      title: "Actions",
      render: (_, record) => (
        <>
          <Button
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
            style={{ marginRight: 8 }}
          />
          <Button
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleDelete(record.member_id)}
          />
        </>
      ),
    },
  ];

  return (
    <ErrorBoundary>
      <div style={{ padding: 20 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
          style={{ marginBottom: 20 }}
        >
          Add New Member
        </Button>

        {loading ? (
          <Spin />
        ) : error ? (
          <Alert
            message="Error fetching members"
            description={error}
            type="error"
            showIcon
          />
        ) : (
          <Table
            columns={columns}
            dataSource={members}
            rowKey="member_id"
            bordered
          />
        )}

        <Modal
          title={editingMember ? "Edit Member" : "Add New Member"}
          open={isModalVisible}
          onCancel={() => setIsModalVisible(false)}
          onOk={handleSubmit}
        >
          <Form form={form} layout="vertical">
            <Form.Item
              name="full_name"
              label="Full Name"
              rules={[{ required: true, message: "Enter full name" }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="email"
              label="Email"
              rules={[{ required: true, message: "Enter email" }]}
            >
              <Input type="email" />
            </Form.Item>
            <Form.Item
              name="password"
              label="Password"
              rules={
                editingMember
                  ? []
                  : [{ required: true, message: "Enter password" }]
              }
            >
              <Input.Password />
            </Form.Item>
            <Form.Item
              name="role"
              label="Role"
              rules={[{ required: true, message: "Select a role" }]}
            >
              <Select placeholder="Select role">
                <Option value="admin">Admin</Option>
                <Option value="staff">Staff</Option>
              </Select>
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

export default ManageAdministrators;
