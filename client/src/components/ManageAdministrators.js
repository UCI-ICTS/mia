// src/components/ManageAdministrators.js

import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import dayjs from "dayjs";
import {
  fetchUsers,
  addUser,
  updateUser,
  deleteUser,
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
  const { staff = [], loading, error } = useSelector(
    (state) => state.data || {}
  );

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingMember, setEditingMember] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    dispatch(fetchUsers()).catch(() =>
      message.error("Failed to load members")
    );
  }, [dispatch]);

  const handleOpenModal = (member = null) => {
    setEditingMember(member);
    form.setFieldsValue({
      first_name: member?.first_name || "",
      last_name: member?.last_name || "",
      email: member?.email || "",
      password: "", // Don't preload password
      role: staff?.is_superuser ? "admin" : staff?.is_staff ? "staff" : "staff",
    });
    setIsModalVisible(true);
  };
  

  const handleSubmit = async () => {
    const values = await form.validateFields();
  
    // ✅ Split full name into first and last name
    const nameParts = values.full_name.trim().split(" ");
    const first_name = nameParts[0] || "";
    const last_name = nameParts.slice(1).join(" ") || "";
  
    const updatedValues = {
      ...values,
      first_name,
      last_name,
      is_superuser: values.role === "admin",
      is_staff: values.role === "admin" || values.role === "staff",
    };
  
    // Remove full_name from payload
    delete updatedValues.full_name;
    delete updatedValues.role;
  
    if (editingMember) {
      await dispatch(updateUser({ id: editingMember.username, ...updatedValues }));
      message.success("Staff updated.");
    } else {
      await dispatch(addUser(updatedValues));
      message.success("Staff added.");
    }
  
    setIsModalVisible(false);
    dispatch(fetchUsers());
  };
  
  

  const handleDelete = async (id) => {
    await dispatch(deleteUser(id));
    message.success("Staff deleted.");
    dispatch(fetchUsers());
  };

  const columns = [
    {
      title: "Name",
      key: "name",
      render: (text, record) => `${record.first_name} ${record.last_name}`,
    },
    { title: "Email", dataIndex: "email" },
    { 
      title: "Role",
      render: (_, record) => (record.is_superuser ? "Admin" : record.is_staff ? "Staff" : "User"),
      dataIndex: "role"
    },
    {
      title: "Date Joined",
      dataIndex: "date_joined",
      render: (date) => date ? dayjs(date).format("MMM D, YYYY h:mm A") : "N/A",
    },
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
            onClick={() => handleDelete(record.username)}
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
          Add New Staff
        </Button>

        {loading ? (
          <Spin />
        ) : error ? (
          <Alert
            message="Error fetching staff"
            description={error}
            type="error"
            showIcon
          />
        ) : (
          <Table
            columns={columns}
            dataSource={staff}
            rowKey="username"
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
