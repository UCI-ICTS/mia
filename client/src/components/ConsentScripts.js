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
import { PlusOutlined, EditOutlined, DeleteOutlined, ReadOutlined, MenuUnfoldOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";

const ConsentScripts = () => {
  const dispatch = useDispatch();
  const { scripts = [], loading, error } = useSelector((state) => state.data || {});
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingScript, setEditingScript] = useState(null);
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
              // onClick={() => handleOpenModal(record)}
              style={{ marginRight: 8 }}
            />
          </Tooltip>
          <Tooltip title="View consent script content">
            <Button
              icon={<ReadOutlined />}
              // onClick={() => handleOpenModal(record)}
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
          </Form>
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

export default ConsentScripts;
