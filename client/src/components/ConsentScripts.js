// src/components/ConsentScripts.js

import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchScripts, addScript, editScript, deleteScript } from "../slices/dataSlice";
import {
  Alert,
  Button,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Table,
  Tooltip,
  Spin,
  message,
} from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, ReadOutlined, MenuUnfoldOutlined, UploadOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";
import { useNavigate } from "react-router-dom";
import UploadModal from "./UploadModal";

const ConsentScripts = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { scripts = [], loading, error } = useSelector((state) => state.data || {});
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingScript, setEditingScript] = useState(null);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    dispatch(fetchScripts()).catch((err) => {
      message.error(err?.message || "Failed to load scripts.");
    });
  }, [dispatch]);

  const handleOpenModal = (script = null) => {
    setEditingScript(script);
    form.setFieldsValue(script || { name: "", description: "" });
    setIsModalVisible(true);
  };

  const handleUpload = async (file) => {
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
  
      const scriptPayload = {
        name: parsed.name || "Uploaded Script",
        description: parsed.description || "Imported from JSON",
        script: parsed, // assuming parsed is the full script graph
      };
  
      await dispatch(addScript(scriptPayload)).unwrap();
      message.success("Script uploaded successfully.");
      dispatch(fetchScripts());
      setUploadModalVisible(false);
      setIsModalVisible(false);
      form.resetFields();
    } catch (err) {
      console.error("Upload error:", err);
      message.error("Invalid or corrupt JSON file.");
    }
    return false; // prevent default upload
  };
  

  const handleSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editingScript) {
        await dispatch(editScript({ id: editingScript.consent_id, ...values })).unwrap();
        message.success("Script updated successfully.");
      } else {
        await dispatch(addScript(values)).unwrap();
        message.success("Script added successfully.");
      }
      setIsModalVisible(false);
      form.resetFields();
      dispatch(fetchScripts());
    } catch (err) {
      message.error(err?.message || "Error saving script.");
    }
  };

  const handleDelete = async (id) => {
    try {
      await dispatch(deleteScript(id)).unwrap();
      message.success("Script deleted.");
      dispatch(fetchScripts());
    } catch (err) {
      message.error(err?.message || "Failed to delete script.");
    }
  };

  const columns = [
    { title: "Name", dataIndex: "name" },
    { title: "Description", dataIndex: "description" },
    { title: "Created", dataIndex: "created_at" },
    {
      title: "Actions",
      render: (_, record) => (
        <>
          <Tooltip title="Edit metadata">
            <Button
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
              style={{ marginRight: 8 }}
            />
          </Tooltip>
          <Tooltip title="Edit content">
            <Button
              icon={<MenuUnfoldOutlined />}
              onClick={() => navigate(`/dashboard/scripts/edit/${record.consent_id}`)}
              style={{ marginRight: 8 }}
            />
          </Tooltip>
          <Tooltip title="View consent script content">
            <Button
              icon={<ReadOutlined />}
              onClick={() => navigate(`/dashboard/scripts/view/${record.consent_id}`)}
              style={{ marginRight: 8 }}
            />
          </Tooltip>
          <Tooltip title="Delete consent script">
            <Popconfirm
              title="Are you sure you want to delete this consent script?"
              onConfirm={() => handleDelete(record.consent_id)} 
              okText="Yes"
              cancelText="No"
            >
              <Button icon={<DeleteOutlined />} danger />
            </Popconfirm>
          </Tooltip>
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
          Add New Script
        </Button>

        {/* === Conditional rendering === */}
        {loading ? (
          <Spin tip="Loading scripts..." style={{ display: "block", textAlign: "center", marginTop: 50 }} />
        ) : error ? (
          <Alert
            message="Error fetching scripts"
            description={error}
            type="error"
            showIcon
            style={{ marginBottom: 20 }}
          />
        ) : scripts?.length === 0 ? (
          <Empty description="No scripts available." />
        ) : (
          <Table
            columns={columns}
            dataSource={scripts}
            rowKey="consent_id"
            bordered
          />
        )}

        {/* Modal for Add/Edit */}
        <Modal
          title={editingScript ? "Edit Script" : "Add New Script"}
          open={isModalVisible}
          onCancel={() => {
            setIsModalVisible(false);
            form.resetFields();
          }}
          onOk={handleSubmit}
        >
          <Form form={form} layout="vertical">
            <Form.Item
              name="name"
              label="Script Name"
              rules={[{ required: true, message: "Please enter script name" }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="description"
              label="Description"
              rules={[{ required: true, message: "Please enter description" }]}
            >
              <Input.TextArea rows={3} />
            </Form.Item>
            <Button
              icon={<UploadOutlined />}
              style={{ marginLeft: 12 }}
              onClick={() => setUploadModalVisible(true)}
            >
              Upload Script
            </Button>
          </Form>
        </Modal>
        <UploadModal
          visible={uploadModalVisible}
          onClose={() => setUploadModalVisible(false)}
          handleUpload={handleUpload}
        />
      </div>
    </ErrorBoundary>
  );
};

export default ConsentScripts;
