// src/components/EditScriptContent.js

import React, { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useSelector } from "react-redux";
import {
  Typography,
  Button,
  Input,
  Select,
  Form,
  Divider,
  Upload,
  message,
  Modal,
} from "antd";
import {
  DownloadOutlined,
  UploadOutlined,
  SaveOutlined,
} from "@ant-design/icons";

const { Title, Paragraph } = Typography;
const { Option } = Select;

const EditScriptContent = () => {
  const { script_id } = useParams();
  const scriptMeta = useSelector((state) =>
    state.data.scripts.find((s) => s.consent_id === script_id)
  );

  const [form] = Form.useForm();
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [editableScriptMap, setEditableScriptMap] = useState(
    scriptMeta?.script || {}
  );

  const rootNodeId = useMemo(() => {
    return Object.keys(editableScriptMap).find((key) => {
      const parents = editableScriptMap[key]?.parent_ids?.map((id) =>
        id.toLowerCase()
      );
      return parents?.includes("start");
    });
  }, [editableScriptMap]);

  const orderedScriptList = useMemo(() => {
    const ordered = [];
    const visited = new Set();

    const walk = (nodeId) => {
      if (!nodeId || visited.has(nodeId)) return;
      visited.add(nodeId);
      const node = editableScriptMap[nodeId];
      if (!node) return;
      ordered.push({ id: nodeId, ...node });
      node.child_ids?.forEach(walk);
    };

    if (rootNodeId) walk(rootNodeId);
    return ordered;
  }, [editableScriptMap, rootNodeId]);

  const handleDownload = () => {
    const file = new Blob([JSON.stringify(editableScriptMap, null, 2)], {
      type: "application/json",
    });
    const element = document.createElement("a");
    element.href = URL.createObjectURL(file);
    element.download = `${scriptMeta.name}_script.json`;
    document.body.appendChild(element);
    element.click();
  };

  const handleUpload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const newScript = JSON.parse(e.target.result);
        setEditableScriptMap(newScript);
        message.success("Script uploaded successfully!");
        setUploadModalVisible(false);
      } catch (err) {
        message.error("Invalid JSON file");
      }
    };
    reader.readAsText(file);
    return false;
  };

  const handleAddMessage = (values) => {
    const newId = `temp-${Date.now()}`;
    const parentIds = values.parent_ids
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);

    const newNode = {
      id: newId,
      type: values.type,
      messages: values.messages.split("\n"),
      parent_ids: parentIds,
      child_ids: [],
    };

    setEditableScriptMap((prev) => {
      const updated = {
        ...prev,
        [newId]: newNode,
      };

      // Update child_ids of parent nodes
      parentIds.forEach((pid) => {
        if (updated[pid]) {
          updated[pid].child_ids = [...(updated[pid].child_ids || []), newId];
        }
      });

      return updated;
    });

    form.resetFields();
    form.setFieldsValue({ parent_ids: newId });
  };

  const handleSaveEdits = () => {
    console.log("Saving script:", editableScriptMap);
    message.success("Script saved (stub). Connect this to your API!");
    // Future: dispatch(saveScriptEdits(script_id, editableScriptMap));
  };

  if (!scriptMeta) {
    return <Paragraph type="danger">Script not found.</Paragraph>;
  }

  return (
    <div style={{ padding: 24 }}>
      <Title level={4}>Edit Script: {scriptMeta.name}</Title>
      <Paragraph type="secondary">
        {scriptMeta.description} (Version {scriptMeta.version_number})
      </Paragraph>

      <div style={{ marginBottom: 20 }}>
        <Button
          icon={<DownloadOutlined />}
          style={{ marginRight: 12 }}
          onClick={handleDownload}
        >
          Download Script
        </Button>
        <Button
          icon={<UploadOutlined />}
          style={{ marginRight: 12 }}
          onClick={() => setUploadModalVisible(true)}
        >
          Upload Script
        </Button>
        <Button icon={<SaveOutlined />} onClick={handleSaveEdits}>
          Save Edits
        </Button>
      </div>

      <Divider />
      <div style={{ display: "flex", gap: 40 }}>
        <div style={{ flex: 1 }}>
          <Form layout="vertical" form={form} onFinish={handleAddMessage}>
            <Form.Item
              name="type"
              label="Message Type"
              rules={[{ required: true }]}
            >
              <Select placeholder="Select type">
                <Option value="bot">Bot</Option>
                <Option value="user">User</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="messages"
              label="Messages (newline separated)"
              rules={[{ required: true }]}
            >
              <Input.TextArea rows={5} />
            </Form.Item>

            <Form.Item
              name="parent_ids"
              label="Parent ID(s)"
              rules={[{ required: true }]}
            >
              <Input />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                Add Message
              </Button>
            </Form.Item>
          </Form>
        </div>

        <div style={{ flex: 1 }}>
          <Title level={5}>Script Entries</Title>
          {orderedScriptList.map((node) => (
            <div
              key={node.id}
              style={{
                background: node.type === "bot" ? "#e0f2f1" : "#e3f2fd",
                padding: 12,
                borderRadius: 6,
                marginBottom: 12,
              }}
            >
              <b>Type:</b> {node.type}
              <br />
              <b>ID:</b> {node.id}
              <br />
              <b>Parent IDs:</b> {node.parent_ids.join(", ")}
              <br />
              <b>Messages:</b>
              {node.messages.map((msg, i) => (
                <div key={i}>{msg}</div>
              ))}
            </div>
          ))}
        </div>
      </div>

      <Modal
        open={uploadModalVisible}
        title="Upload Script JSON"
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
      >
        <Upload
          beforeUpload={handleUpload}
          accept=".json"
          showUploadList={false}
        >
          <Button icon={<UploadOutlined />}>Select JSON File</Button>
        </Upload>
      </Modal>
    </div>
  );
};

export default EditScriptContent;
