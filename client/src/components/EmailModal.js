// src/components.EmailModal.js

import "../style.css";
import { Modal, Form, Input, Button, message } from "antd";
import { useDispatch } from "react-redux";
import { sendDocument } from "../slices/dataSlice";

const { TextArea } = Input;


const EmailModal = ({ visible, onClose, docInfo = {} }) => {
  const dispatch = useDispatch();
  const [form] = Form.useForm();
  
  const handleFinish = (values) => {
    const doc_id = docInfo.id
    dispatch(sendDocument({
        "id": doc_id,
        "from": values.from,
        "email": values.email,
        "body": values.body,
        "subject": values.subject
    }))
      .then((data) => {
        console.log('Data fetched successfully:', data);
        message.success("Email sent")
      })
      .catch((error) => {
        console.error('Error fetching data:', error);
        message.error('Error fetching data:', error)
      });

    form.resetFields();
    onClose();
  };
  
  return (
    <Modal
      title="Email Consent Document"
      open={visible}
      onCancel={onClose}
      footer={null}
      className="uci-modal"
    >
      <Form
        layout="vertical"
        form={form}
        initialValues={{
          from:  "",
          email:  "",
          body: "",
          subject: docInfo.file_name,
        }}
        onFinish={handleFinish}
      >
        <Form.Item name="from" label="From" rules={[{ type: "email" }]}>
          <Input />
        </Form.Item>
        <Form.Item name="email" label="To" rules={[{ required: true, type: "email" }]}>
          <Input />
        </Form.Item>
        <Form.Item name="body" label="Email Body" >
          <TextArea rows={4} />
        </Form.Item>
        <Form.Item name="subject" label="Email Subject" >
          <Input />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">
            Submit Request
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default EmailModal;
