// src/components/ManageParticipants.js

import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import dayjs from "dayjs";
import { fetchUsers, addUser, deleteUser, updateUser, getInviteLink, generateInviteLink } from "../slices/dataSlice";
import {
  Alert,
  Button,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Spin,
  Table,
  Tag,
  Tooltip,
  message,
} from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  LinkOutlined,
  UserAddOutlined,
  CopyOutlined,
  ReloadOutlined
} from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";

const ManageParticipants = () => {
  const dispatch = useDispatch();
  const { 
    participants = [],
    scripts = [],
    loading,
    error
  } = useSelector((state) => state.data || {});
  const [isModalVisible, setModalVisible] = useState(false);
  const [isEditModalVisible, setEditModalVisible] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [form] = Form.useForm();

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

  const handleGetInviteLink = async (username) => {
    try {
      const result = await dispatch(getInviteLink(username)).unwrap();
  
      if (!result?.invite_link) {
        Modal.info({
          title: "No Invite Link",
          content: "This user does not have an invite link available.",
        });
        return;
      }
  
      Modal.info({
        title: "Invite Link",
        content: (
          <Input
            value={result.invite_link}
            addonAfter={
              <CopyOutlined
                onClick={() => {
                  navigator.clipboard.writeText(result.invite_link);
                  message.success("Copied to clipboard!");
                }}
                style={{ cursor: "pointer" }}
              />
            }
            readOnly
          />
        ),
      });
    } catch (err) {
      const status = err?.status;
      const msg =
        status === 404
          ? "Invite link not found for this user."
          : err?.msg || "Failed to fetch invite link.";
      message.error(msg);
    }
  };
  
  const handleGenerateNewInviteLink = async (username) => {
    try {
      await dispatch(generateInviteLink(username)).unwrap();
      message.success("Invite link generated.");
    } catch (err) {
      message.error("Failed to generate link.");
    }
  };
  
  const handleDelete = async (username) => {
    try {
      await dispatch(deleteUser(username)).unwrap();
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
      title: "Invite Status",
      dataIndex: "invite_expired",
      render: (invite) =>
        invite ? (
          <Tag color="red">Expired/DNE</Tag>
        ) : (
          <Tag color="green">Valid</Tag>
        ),
    },
    {
      title: "Consent Started",
      dataIndex: "created_at",
      render: (created_at) =>
        created_at ? (
          <Tag color="green">{dayjs(created_at).format("MMM D, YYYY h:mm A")}</Tag>
        ) : (
          <Tag color="red">No</Tag>
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
          <Tooltip title="Edit participant">
            <Button
              icon={<EditOutlined />}
              style={{ marginRight: 8 }}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="Get invite link">
            <Button
              icon={<LinkOutlined />}
              style={{ marginRight: 8 }}
              onClick={() => handleGetInviteLink(record.username)}
              disabled={record.invite_expired}
            />
          </Tooltip>
          <Tooltip title="Gernerate new invite link">
            <Button
              icon={<ReloadOutlined />}
              style={{ marginRight: 8 }}
              onClick={() => {handleGenerateNewInviteLink(record.username)}}
            />
          </Tooltip>
          <Tooltip title="Delete participant">
            <Popconfirm
              title="Are you sure you want to delete this user?"
              onConfirm={() => handleDelete(record.username)} 
              okText="Yes"
              cancelText="No"
            >
              <Button icon={<DeleteOutlined />} danger />
            </Popconfirm>
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
          rowKey={(record) => record.username}
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
            <Form.Item
              name="script_id"
              label="Consent Script"
              rules={[{ required: true, message: "Please select a consent script" }]}
            >
              <Select placeholder="Select a consent script">
                {scripts.map((script) => (
                  <Select.Option key={script.script_id} value={script.script_id}>
                    {script.name} (v{script.version_number})
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Form>
        </Modal>
        
        {/* Edit User Modal */}
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
