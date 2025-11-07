// src/components/UploadModal.js

import "../style.css"
import { Modal, Upload, Button } from "antd";
import { UploadOutlined } from "@ant-design/icons";

const UploadModal = ({ visible, onClose, handleUpload }) => {
  return (
    <Modal
      className="uci-modal"
      open={visible}
      title="Upload Script JSON"
      onCancel={onClose}
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
  );
};

export default UploadModal;