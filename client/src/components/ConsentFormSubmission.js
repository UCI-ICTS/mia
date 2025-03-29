import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { submitConsentForm } from "../slices/dataSlice";
import { Button, Input, Checkbox, Radio, Select, Typography, Form, Space } from "antd";
import ErrorBoundary from "antd/es/alert/ErrorBoundary";
const { TextArea } = Input;
const { Title, Paragraph } = Typography;

const ConsentFormSubmission = ({ form, invite_id }) => {
  const dispatch = useDispatch();
  const [formValues, setFormValues] = useState({});
  const [formInstance] = Form.useForm();
  const [, formDef] = form[0]; // Safe destructuring

  const handleFinish = (values) => {
    const formatted = Object.entries(values).map(([name, value]) => ({
      name,
      value
    }));

    dispatch(submitConsentForm({
      invite_id,
      node_id: form.node_id,
      form_type: form.form_type || "generic",
      form_responses: formatted
    }));
  };
  console.log("form ", formDef)
  return (
    <Form
      form={formInstance}
      layout="vertical"
      onFinish={handleFinish}
      style={{ maxWidth: 700, margin: "0 auto", marginTop: 24 }}
    >
      {/* Optional Form Description */}
      {formDef.description && (
        <>
          {Array.isArray(form.description)
            ? form.description.map((line, idx) => <Paragraph key={idx}>{line}</Paragraph>)
            : <Paragraph>{form.description}</Paragraph>
          }
        </>
      )}

      {formDef.fields.map((field) => {
        const commonProps = {
          name: field.name,
          label: field.label,
          rules: field.required ? [{ required: true, message: `Please complete "${field.label}"` }] : []
        };

        switch (formDef.type) {
          case "input":
            return (
              <Form.Item key={field.name} {...commonProps}>
                <Input
                  type={field.input_type || "text"}
                  placeholder={field.placeholder}
                  pattern={field.pattern}
                />
              </Form.Item>
            );

          case "textarea":
            return (
              <Form.Item key={field.name} {...commonProps}>
                <TextArea rows={4} placeholder={field.placeholder} />
              </Form.Item>
            );

          case "checkbox":
            return (
              <Form.Item key={field.name} valuePropName="checked" {...commonProps}>
                <Checkbox>{field.label}</Checkbox>
              </Form.Item>
            );

            case "checkbox_group":
              const checkboxOptions = field.fields?.map((f) => ({
                label: f.label,
                value: f.value
              })) || [];
            console.log(checkboxOptions)
              return (
                <Form.Item key={field.name} {...commonProps}>
                  <Checkbox.Group
                    options={checkboxOptions}
                    style={{ display: "flex", flexDirection: "column", gap: 8 }}
                  />
                </Form.Item>
              );
            

          case "radio":
            return (
              <Form.Item key={field.name} {...commonProps}>
                <Radio.Group>
                  <Space direction="vertical">
                    {field.options?.map((opt) => (
                      <Radio key={opt.value} value={opt.value}>
                        {opt.label}
                      </Radio>
                    ))}
                  </Space>
                </Radio.Group>
              </Form.Item>
            );

          case "select":
            return (
              
              <Form.Item key={field.name} {...commonProps}>
                <Select placeholder={`Select ${field.label}`}>
                  {field.options?.map((opt) => (
                    <Select.Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            );

          default:
            return null;
        }
      })}

      <Form.Item style={{ textAlign: "center" }}>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};

export default ConsentFormSubmission;
