// src/pages/DocumentsPage.js

import "../style.css";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchDocuments } from "../slices/dataSlice";
import { Table, Typography, Button, Tag, Spin, Alert, message, Tooltip } from "antd";
import { MailOutlined, DownloadOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";
import FollowUpFormModal from "../components/FollowUpModal";

const { Title } = Typography;

const DocumentsPage = () => {
  const dispatch = useDispatch();
  const [contactModalVisible, setContactModalVisible] = useState(false);
  const { documents = [], loading, error } = useSelector((state) => state.data || {});

  useEffect(() => {
    if (!loading && !error && (!documents || documents.length === 0)) {
      dispatch(fetchDocuments());
    }
  }, [documents, loading, error, dispatch]);
  
  const handleDownload = async () => {};
  if (error) return <Alert message="Error fetching follow-ups" description={error} type="error" showIcon />;

  const columns = [
    { title: "Name", dataIndex: "username"},
    { title: "File Name", dataIndex: "file_name"},
    { title: "Session ID", dataIndex: "session"},
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <>
         <Tooltip title="View or download the PDF">
            <Button
              icon={<DownloadOutlined />}
              style={{ marginRight: 8 }}
              onClick={()=> window.open(record.file_url, "_blank")}
            />
         </Tooltip>
         <Tooltip title="Send document via email">
            <Button
              icon={<MailOutlined />}
              style={{ marginRight: 8 }}
              onClick={() => handleDownload(record)}
            />
         </Tooltip>
        </>
      )
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
            >Add Participant Document</Button>
          </div>
          <Title level={3} className="primary-title">Participant Documents</Title>
        </div>
        <hr />
        <Table
          className="table"
          columns={columns}
          dataSource={documents || []}
          rowKey="id"
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

export default DocumentsPage;
