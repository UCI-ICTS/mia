// src/pages/FollowUp.js

import "../style.css";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchFollowUps, resolveFollowUp } from "../slices/dataSlice";
import { Table, Typography, Button, Tag, Spin, Alert, message } from "antd";
import { CheckCircleOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";
import FollowUpFormModal from "../components/FollowUpModal";

const { Title } = Typography;

const FollowUp = () => {
  const dispatch = useDispatch();
  const [contactModalVisible, setContactModalVisible] = useState(false);
  const { followUps = [], loading, error } = useSelector((state) => state.data || {});

  if (loading) return <Spin tip="Loading follow-ups..." style={{ display: "block", textAlign: "center", marginTop: 50 }} />;
  if (error) return <Alert message="Error fetching follow-ups" description={error} type="error" showIcon />;

  const handleResolve = async (id) => {
    await dispatch(resolveFollowUp(id));
    message.success("Marked as resolved!");
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
      filters: [
        {
          text: 'Resolved',
          value: true,
        },
        {
          text: 'Unresolved',
          value: false,
        },
      ],
      onFilter: (value, record) => record.resolved === value,
    },
    { title: "Created", dataIndex: "created_at" },
    {
      title: "Actions",
      render: (_, record) =>
        !record.resolved ? (
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={() => handleResolve(record.user_follow_up_id)}
          >
            Mark as Resolved
          </Button>
        ) : (
          <Tag color="green">Resolved</Tag>
        ),
    },
  ];

  return (
    <ErrorBoundary>
      <div className="layout">
        <div className="primary-header">
          <div>
            <Button
              // icon={<UserAddOutlined />}
              className="header-button"
              onClick={() => setContactModalVisible(true)}
            >Add Participant Follow Up</Button>
          </div>
          <Title level={3} className="primary-title">Participant Foll Up</Title>
        </div>
        <hr />
        <Table
          className="table"
          columns={columns}
          dataSource={followUps || []}
          rowKey="user_follow_up_id"
          bordered
          loading={loading}
        />
      </div>
      <FollowUpFormModal 
        visible={contactModalVisible}
        onClose={() => {setContactModalVisible(false)}}
      />
    </ErrorBoundary>
  );
};

export default FollowUp;
