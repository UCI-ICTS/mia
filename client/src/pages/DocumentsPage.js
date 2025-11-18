// src/pages/DocumentsPage.js

import "../style.css";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchDocuments } from "../slices/dataSlice";
import { Table, Typography, Button, Alert, Tooltip } from "antd";
import { MailOutlined, DownloadOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";
import EmailModal from "../components/EmailModal";

const { Title } = Typography;

const DocumentsPage = () => {
  const dispatch = useDispatch();
  const [emailModalVisible, setEmailModalVisible] = useState(false);
  const [docInfo, setDocInfo] = useState();
  const { documents = [], participants = [], loading, error } = useSelector((state) => state.data || {});

  useEffect(() => {
    if (!loading && !error && (!documents || documents.length === 0)) {
      dispatch(fetchDocuments());
    }
  }, [documents, loading, error, dispatch]);
  
  const handleEmail = async (doc) => {
    setEmailModalVisible(true)
    setDocInfo(doc)
  };

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
              onClick={() => handleEmail(record)}
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
              onClick={() => console.log("stuff")}
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
      
      <EmailModal
        visible={emailModalVisible}
        onClose={() => {setEmailModalVisible(false)}}
        docInfo = {docInfo}
      />
    </ErrorBoundary>
  );
};

export default DocumentsPage;
