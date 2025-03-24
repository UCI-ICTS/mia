// src/components/ManageParticipants.js

import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import dayjs from "dayjs";
import { fetchUsers, addUser, deleteUser, updateUser } from "../slices/dataSlice";
import {
  Alert,
  Button,
  Dropdown,
  Form,
  Input,
  Menu,
  Modal,
  Spin,
  Table,
  Tag,
  Tooltip,
  message,
} from "antd";
import {
  DeleteOutlined,
  DownOutlined,
  EditOutlined,
  LinkOutlined,
  UserAddOutlined,
} from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";

const ManageParticipants = () => {
  const dispatch = useDispatch();
  const { participants = [], loading, error } = useSelector((state) => state.data || {});
  const [isModalVisible, setModalVisible] = useState(false);
  const [isEditModalVisible, setEditModalVisible] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    if (dispatch) dispatch(fetchUsers()).catch(() => message.error("Failed to load participantss."));
  }, [dispatch]);

  const handleAddUser = async () => {
    try {
      const values = await form.validateFields();
      await dispatch(addUser({ ...values, is_staff: false })).unwrap();
      message.success("Participant added successfully!");
      setModalVisible(false);
      form.resetFields();
    } catch (err) {
      message.error(err?.message || "Error adding participant");
    }
  };

  const handleSubmitEdit = async () => {
    try {
      const values = await form.validateFields();
      await dispatch(
        updateUser({ username: editingUserId, ...values })
      ).unwrap();
      message.success("Participant updated successfully!");
      setEditModalVisible(false);
      setEditingUserId(null);
      form.resetFields();
      dispatch(fetchUsers());
    } catch (err) {
      message.error(err?.message || "Failed to update participant");
    }
  };
  
  const handleEdit = (user) => {
    form.setFieldsValue({
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      phone: user.phone,
    });
    setEditingUserId(user.username);
    setEditModalVisible(true);
  };
  
  const handleGetInviteLink = async (userId) => {
    try {
      const res = await fetch(`/api/users/${userId}/chat_url/`);
      const data = await res.json();
      Modal.info({
        title: "Invite Link",
        content: data.text || "No invite URL available",
      });
    } catch (err) {
      message.error("Failed to fetch invite link");
    }
  };
  
  const handleGenerateNewInviteLink = async (userId) => {
    try {
      await fetch(`/api/users/${userId}/regenerate_chat_url/`, { method: "POST" });
      message.success("New invite link generated.");
      dispatch(fetchUsers());
    } catch (err) {
      message.error("Failed to generate new link");
    }
  };
  
  const handleDelete = async (userId) => {
    try {
      await dispatch(deleteUser(userId)).unwrap();
      message.success("Participant deleted.");
      dispatch(fetchUsers());
    } catch (err) {
      message.error("Failed to delete participant.");
    }
  };
  
  const columns = [
    {
      title: "Name",
      dataIndex: "first_name",
      render: (text, record) => `${record.first_name} ${record.last_name}`,
    },
    { title: "Email", dataIndex: "email" },
    {
      title: "Phone",
      dataIndex: "phone",
      render: (text) => text || "N/A",
    },
    {
      title: "Consent Status",
      dataIndex: "consent_complete",
      render: (consent) =>
        consent ? (
          <Tag color="green">Complete</Tag>
        ) : (
          <Tag color="red">Pending</Tag>
        ),
    },
    {
      title: "Date Joined",
      dataIndex: "date_joined",
      render: (date) => date ? dayjs(date).format("MMM D, YYYY h:mm A") : "N/A",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <>
          <Tooltip title="Get invite link">
            <Button
              icon={<LinkOutlined />}
              style={{ marginRight: 8 }}
              onClick={() => handleGetInviteLink(record.id)}
              />
          </Tooltip>
          <Tooltip title="Edit participant">
            <Button
              icon={<EditOutlined />}
              style={{ marginRight: 8 }}
              onClick={() => handleEdit(record)}
              />
          </Tooltip>
          <Tooltip title="Gernerate new invite link">
            <Button
              icon={<UserAddOutlined />}
              style={{ marginRight: 8 }}
              onClick={() => handleGenerateNewInviteLink(record.id)}
              />
          </Tooltip>
          <Tooltip title="Delete participant">
            <Button
              icon={<DeleteOutlined />}
              danger
              onClick={() => handleDelete(record.id)}
              />
          </Tooltip>
        </>
      ),
    }    
  ];

  if (loading) return <Spin tip="Loading users..." style={{ display: "block", textAlign: "center", marginTop: 50 }} />;
  if (error) return <Alert message="Error fetching users" description={error} type="error" showIcon />;

  return (
    <ErrorBoundary>
      <div style={{ padding: 20 }}>
        <Button
          type="primary"
          icon={<UserAddOutlined />}
          style={{ marginBottom: 20 }}
          onClick={() => setModalVisible(true)}
        >
          Add New Participant
        </Button>
        
        <Table
          columns={columns}
          dataSource={participants || []}
          rowKey="username"
          bordered
        />

        {/* Add User Modal */}
        <Modal
          title="Add New Participant"
          open={isModalVisible}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
          }}
          onOk={handleAddUser}
          okText="Add Participant"
        >
          <Form form={form} layout="vertical">
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
          </Form>
        </Modal>
        
        <Modal
          title="Edit Participant"
          open={isEditModalVisible}
          onCancel={() => {
            setEditModalVisible(false);
            form.resetFields();
            setEditingUserId(null);
          }}
          onOk={handleSubmitEdit}
          okText="Submit Edits"
        >
          <Form form={form} layout="vertical">
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
          </Form>
        </Modal>
    
      </div>
    </ErrorBoundary>

    
  );
};

export default ManageParticipants;
