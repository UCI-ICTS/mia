// src/components/ConsentScripts.js 

import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchScripts, addScript, editScript, deleteScript } from "../slices/dataSlice";
import { Table, Button, Modal, Input, Form, message, Spin, Alert } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";

const ConsentScripts = () => {
  const dispatch = useDispatch();
  const { scripts = [], loading, error } = useSelector((state) => state.data || {});
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingScript, setEditingScript] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    dispatch(fetchScripts()).catch(() => message.error("Failed to load scripts."));
  }, [dispatch]);

  if (loading) return <Spin tip="Loading scripts..." style={{ display: "block", textAlign: "center", marginTop: 50 }} />;
  if (error) return <Alert message="Error fetching scripts" description={error} type="error" showIcon />;

  const handleOpenModal = (script = null) => {
    setEditingScript(script);
    form.setFieldsValue(script || { name: "", description: "" });
    setIsModalVisible(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingScript) {
      await dispatch(editScript({ id: editingScript.consent_id, ...values }));
      message.success("Script updated successfully.");
    } else {
      await dispatch(addScript(values));
      message.success("Script added successfully.");
    }
    setIsModalVisible(false);
    dispatch(fetchScripts());
  };

  const handleDelete = async (id) => {
    await dispatch(deleteScript(id));
    message.success("Script deleted.");
    dispatch(fetchScripts());
  };

  const columns = [
    { title: "Name", dataIndex: "name" },
    { title: "Description", dataIndex: "description" },
    { title: "Created", dataIndex: "created_at" },
    {
      title: "Actions",
      render: (_, record) => (
        <>
          <Button icon={<EditOutlined />} onClick={() => handleOpenModal(record)} style={{ marginRight: 8 }} />
          <Button icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.consent_id)} />
        </>
      ),
    },
  ];

  return (
    <ErrorBoundary>
      <div style={{ padding: 20 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()} style={{ marginBottom: 20 }}>
          Add New Script
        </Button>
        <Table columns={columns} dataSource={scripts || []} rowKey="consent_id" bordered />

        {/* Modal for Adding/Editing Scripts */}
        <Modal title={editingScript ? "Edit Script" : "Add New Script"} open={isModalVisible} onCancel={() => setIsModalVisible(false)} onOk={handleSubmit}>
          <Form form={form} layout="vertical">
            <Form.Item name="name" label="Script Name" rules={[{ required: true, message: "Please enter script name" }]}>
              <Input />
            </Form.Item>
            <Form.Item name="description" label="Description" rules={[{ required: true, message: "Please enter description" }]}>
              <Input.TextArea rows={3} />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

export default ConsentScripts;
