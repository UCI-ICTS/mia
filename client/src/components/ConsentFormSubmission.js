import React from "react";
import { useDispatch } from "react-redux";
import { Form, Checkbox, Button, Space, Radio } from "antd";
import { submitConsentForm } from "../slices/dataSlice";

const ConsentFormSubmission = ({ form, invite_id }) => {
  const dispatch = useDispatch();
  const [formInstance] = Form.useForm();

  const handleFinish = (values) => {
    // Convert all form values to { name, value } pairs
    const checkedNames = values.checkbox_group || [];
    const formatted = Object.entries(values).map(([name, value]) => ({
      name,
      value
    }));
    console.log(invite_id, form.node_id,form.form_type, checkedNames)
    dispatch(
      submitConsentForm({
        invite_id,
        node_id: form.id_node || form.node_id, // support both
        form_type: form.form_type || form.type || "generic",
        form_responses: checkedNames,
      })
    );
  };
  

  const formType = form.type;
  console.log(form)
  return (
    <Form
      form={formInstance}
      layout="vertical"
      onFinish={handleFinish}
      style={{ maxWidth: 700, margin: "0 auto", marginTop: 24 }}
    >
      {formType === "checkbox_group" && (
        <Form.Item
          name="checkbox_group"
          label="Who might consider enrolling?"
          rules={[{ required: true, message: "Please select at least one option" }]}
        >
          <Checkbox.Group>
            <Space direction="vertical">
              {form.fields.map((f) => (
                <Checkbox key={f.value} value={f.name}>
                  {f.label}
                </Checkbox>
              ))}
            </Space>
          </Checkbox.Group>
        </Form.Item>
      )}

      {formType === "radio" && (
        <Form.Item
          name="radio_selection"
          label="Please choose one"
          rules={[{ required: true, message: "Please select an option" }]}
        >
          <Radio.Group>
            <Space direction="vertical">
              {form.fields.map((f) => (
                <Radio key={f.value} value={f.name}>
                  {f.label}
                </Radio>
              ))}
            </Space>
          </Radio.Group>
        </Form.Item>
      )}

      {/* Add more formType conditions like 'input', 'textarea', etc. as needed */}

      <Form.Item style={{ textAlign: "center" }}>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};

export default ConsentFormSubmission;
