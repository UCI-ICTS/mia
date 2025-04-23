// src/FollowUp.js

import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchFollowUps, resolveFollowUp } from "../slices/dataSlice";
import { Table, Button, Tag, Spin, Alert, message, Popconfirm, Tooltip } from "antd";
import { CheckCircleOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";

const FollowUp = () => {
  const dispatch = useDispatch();
  const { followUps = [], loading, error } = useSelector((state) => state.data || {});

  if (loading) return <Spin tip="Loading follow-ups..." style={{ display: "block", textAlign: "center", marginTop: 50 }} />;
  if (error) return <Alert message="Error fetching follow-ups" description={error} type="error" showIcon />;

  const handleResolve = (id) => {
    dispatch(resolveFollowUp(id));
    dispatch(fetchFollowUps()); // Refresh list
  };

  const columns = [
    { title: "Name", dataIndex: "first_name", render: (text, record) => `${record.first_name} ${record.last_name}` },
    { title: "Email", dataIndex: "email" },
    { title: "Phone", dataIndex: "phone", render: (text) => text || "N/A" },
    { title: "Consent", dataIndex: "consent_name", render: (text, record) => `${record.consent_script_name} ${record.consent_script_version}`|| "..." },
    { title: "Reason", dataIndex: "follow_up_reason" },
    { title: "More Info", dataIndex: "follow_up_info" },
    {
      title: "Resolved",
      dataIndex: "resolved",
      render: (resolved) => (resolved ? <Tag color="green">Resolved</Tag> : <Tag color="red">Unresolved</Tag>),
    },
    { title: "Created", dataIndex: "created_at" },
    {
      title: "Actions",
      render: (_, record) =>
        !record.resolved ? (
          <>
          <Tooltip title="Delete participant">
            <Popconfirm
              title="Are you sure you want to resolve this item?"
              onConfirm={() => handleResolve(record.user_follow_up_id)} 
              okText="Yes"
              cancelText="No"
            >
              <Button
                type="primary"
                icon={<CheckCircleOutlined />}
              >Mark as Resolved</Button>
            </Popconfirm>
          </Tooltip>
          </>
        ) : (
          <Tag color="green">Resolved</Tag>
        ),
    },
  ];

  return (
    <ErrorBoundary>
      <div style={{ padding: 20 }}>
        <Table
          columns={columns}
          dataSource={followUps || []}
          rowKey="user_follow_up_id"
          bordered
          loading={loading}
        />
      </div>
    </ErrorBoundary>
  );
};

export default FollowUp;
