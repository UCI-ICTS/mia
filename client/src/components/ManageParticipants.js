import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchUsers } from "../slices/dataSlice";
import { Table, Button, Tag, message, Spin, Alert } from "antd";
import { UserAddOutlined, EditOutlined, DeleteOutlined, LinkOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary"; // ✅ Import ErrorBoundary

const ManageParticipants = () => {
  const dispatch = useDispatch();
  const { users = [], loading, error } = useSelector((state) => state.data || {}); // ✅ Prevents destructuring error

  useEffect(() => {
    if (dispatch) dispatch(fetchUsers()).catch(() => message.error("Failed to load users."));
  }, [dispatch]);

  if (loading) return <Spin tip="Loading users..." style={{ display: "block", textAlign: "center", marginTop: 50 }} />;
  if (error) return <Alert message="Error fetching users" description={error} type="error" showIcon />;

  return (
    <ErrorBoundary>
      <div style={{ padding: 20 }}>
        <Button type="primary" icon={<UserAddOutlined />} style={{ marginBottom: 20 }}>
          Add New User
        </Button>
        <Table
          columns={[
            { title: "Name", dataIndex: "first_name", render: (text, record) => `${record.first_name} ${record.last_name}` },
            { title: "Email", dataIndex: "email" },
            { title: "Phone", dataIndex: "phone", render: (text) => text || "N/A" },
            { title: "Chat", dataIndex: "chat_name", render: (text) => text || "..." },
            { title: "Consent", dataIndex: "consent_complete", render: (consent) => (consent ? <Tag color="green">Complete</Tag> : <Tag color="red">Pending</Tag>) },
            { title: "Created", dataIndex: "created_at" },
          ]}
          dataSource={users || []} // ✅ Prevents table from crashing if users is undefined
          rowKey="user_id"
          bordered
        />
      </div>
    </ErrorBoundary>
  );
};

export default ManageParticipants;
