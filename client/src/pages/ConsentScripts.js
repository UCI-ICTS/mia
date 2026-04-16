// src/pages/ConsentScripts.js

import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchConsentScripts, addScript, editScript, deleteScript, getConsentScript } from "../slices/dataSlice";
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
  Typography,
  Upload,
  message,
  InputNumber,
} from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, ReadOutlined, MenuUnfoldOutlined, UploadOutlined } from "@ant-design/icons";
import ErrorBoundary from "../components/ErrorBoundary";
import { useNavigate } from "react-router-dom";

const { Title } = Typography; 

const ConsentScripts = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { scripts = [], loading, error } = useSelector((state) => state.data || {});
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingScript, setEditingScript] = useState(null);
  const [fileList, setFileList] = useState([]);

  const [form] = Form.useForm();
  const values = Form.useWatch([], form); //watch all fields

  useEffect(() => {
    dispatch(fetchConsentScripts()).catch((err) => {
      message.error(err?.message || "Failed to load scripts.");
    });
  }, [dispatch]);

  const readJsonFile = (file) => 
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const parsed = JSON.parse(e.target.result);
          resolve(parsed);
        } catch (error) {
          console.log(error);
          reject(new Error("Invalid JSON file."));
        }
      };
      reader.onerror = () => reject(new Error("Failed to read file."));
      reader.readAsText(file);
    });
    
  const handleOpenModal = (script = null) => {
    setEditingScript(script);
    form.setFieldsValue(script || { name: "", description: "" });
    setIsModalVisible(true);
  };

  const handleSubmit = async () => {
    let parsedJson = null;
    console.log("fileList:", fileList, typeof fileList);
    if (Array.isArray(fileList) && fileList.length > 0) {
      const fileObj = fileList[0].originFileObj || fileList[0];

      parsedJson = await readJsonFile(fileObj);
    }
    const payload = {
      ...values,
      ...(parsedJson ? {script: parsedJson} : {}),
    };
    
    try {
      if (editingScript) {
        await dispatch(editScript({ id: editingScript.script_id, ...payload })).unwrap();
        message.success("Script updated successfully.");
      } else {
        await dispatch(addScript(payload)).unwrap();
      }
      setIsModalVisible(false);
      form.resetFields();
      dispatch(fetchConsentScripts());
    } catch (err) {
      message.error(err?.message || "Error saving script.");
    }
  };

  const handleView = async (script_id) => {
    try {
      // Optionally show loading indicator
      message.loading({ content: "Loading script...", key: "loadScript" });

      // Dispatch thunk — unwrap to get real rejection if fails
      await dispatch(getConsentScript(script_id)).unwrap();

      message.success({ content: "Script loaded.", key: "loadScript", duration: 1 });

      // ✅ Navigate after success
      navigate(`/dashboard/scripts/view/${script_id}`);
    } catch (error) {
      console.error("Error fetching script:", error);
      // message.error({ content: "Failed to load consent script.", key: "loadScript" });
    }
  };

  const handleDelete = async (id) => {
    try {
      await dispatch(deleteScript(id)).unwrap();
      // message.success("Script deleted.");
      dispatch(fetchConsentScripts());
    } catch (err) {
      message.error(err?.message || "Failed to delete script.");
    }
  };

  const columns = [
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
          {/* <Tooltip title="Edit content">
            <Button
              icon={<MenuUnfoldOutlined />}
              onClick={() => navigate(`/dashboard/scripts/edit/${record.script_id}`)}
              style={{ marginRight: 8 }}
            />
          </Tooltip> */}
          <Tooltip title="View consent script content">
            <Button
              icon={<ReadOutlined />}
              onClick={() => handleView(record.script_id)}
              style={{ marginRight: 8 }}
              // disabled
            />
          </Tooltip>
          <Tooltip title="Delete consent script">
            <Popconfirm
              title="Are you sure you want to delete this consent script?"
              onConfirm={() => handleDelete(record.script_id)} 
              okText="Yes"
              cancelText="No"
            >
              <Button icon={<DeleteOutlined />} danger />
            </Popconfirm>
          </Tooltip>
        </>
      ),
    },
    { title: "Name", dataIndex: "name" },
    { title: "Description", dataIndex: "description" },
    { title: "Created", dataIndex: "created_at" },
  ];

  return (
    <ErrorBoundary>
      <div className="layout">
        <div className="primary-header">
          <Title className="primary-title">Consentbot Scripts</Title>
        </div>
        {/* === Conditional rendering === */}
        {loading ? (
          <Spin tip="Loading scripts..." fullscreen />
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
          <div>
            <Button
              className="header-button"
              icon={<PlusOutlined />}
              onClick={() => handleOpenModal()}
            >Add New Script</Button>
            <Table
              className="table"
              columns={columns}
              dataSource={scripts}
              rowKey="script_id"
              bordered
            />
          </div>
        )}

        {/* Modal for Add/Edit */}
        <Modal
          title={editingScript ? "Edit Script" : "Add New Script"}
          className="uci-modal"
          open={isModalVisible}
          onCancel={() => {
            setIsModalVisible(false);
            form.resetFields();
          }}
          onOk={handleSubmit}
          // okButtonProps={{disabled: !isReady}}
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
              name="version_number"
              label="Script Version Number"
              rules={[{ required: true, message: "Please enter script version" }]}
            >
              <InputNumber min={0}/>
            </Form.Item>
            <Form.Item
              name="study_info"
              label="Study Information Website"
              rules={[{ required: true, message: "Please enter a study information website" }]}
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
            <Form.Item>
              <Upload
                accept=".json"
                fileList={fileList}
                beforeUpload={(file) =>{
                  setFileList([file]);
                  return false; 
                }}
                onRemove={() => {
                  setFileList([]);
                }}
                maxCount={1}
              >
                <Button icon={<UploadOutlined />}>Select JSON File</Button>
              </Upload>
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

export default ConsentScripts;
