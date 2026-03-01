import React from "react";
import { useDispatch } from "react-redux";
import { Form, Checkbox, Button, Space, Radio, Select, Input, Typography } from "antd";
import { submitConsentForm } from "../slices/consentSlice";


const ConsentFormSubmission = ({ form, session_slug }) => {
  const { Paragraph } = Typography;
  const dispatch = useDispatch();
  const [formInstance] = Form.useForm();

  const handleFinish = (values) => {
    // Convert all form values to { name, value } pairs
    const { anonymize = false, ...formValues } = values
    const checkedNames = values.checkbox_form || [];
    const formatted = Object.entries(values).map(([name, value]) => ({
      name,
      value: value ?? null
    }));
    console.log(session_slug, form.node_id, form.form_type, formatted)
    dispatch(
      submitConsentForm({
        session_slug,
        node_id: form.id_submit_node || form.node_id, // support both
        form_type: form.form_type || "generic",
        form_responses: formatted,
      })
    );
  };
  

  const formType = (form.form_type);
  console.log(formType)
  return (
    <Form
      form={formInstance}
      layout="vertical"
      className="consent-form"
      onFinish={handleFinish}
      style={{ maxWidth: 700, margin: "0 auto", marginTop: 24 }}
    >
      {(formType === "checkbox_form" || formType === "child_ages_checkbox_form" ) && (
        <Form.Item
          name="checkbox_form"
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

      {(formType === "text_fields" || formType=== "contact_other_adult") && (
        <Space direction="vertical">
          {form.fields.map((field) => (
          <Form.Item
            name={field.name}
            label={field.label}
            rules={[{ required: true, message: 'This field is required.' }]}
          >
            <Input.TextArea rows={1} placeholder={`Enter their ${field.name}...`} />
          </Form.Item>
          ))}
        </Space>

      )}

      {formType === "feedback" && (() => {
        const satisfactionField = form.fields[0];
        const suggestionField = form.fields[1];

        return (
          <>
            <Form.Item
              name={satisfactionField.name}
              label={satisfactionField.label}
              rules={[{ required: satisfactionField.required, message: 'This field is required.' }]}
            >
              <Select
                placeholder="Select an option"
                options={satisfactionField.options.map(opt => ({
                  label: opt.label,
                  value: opt.value
                }))}
              />
            </Form.Item>
            
            <Form.Item
              name={suggestionField.name}
              label={suggestionField.label}
            >
              <Input.TextArea rows={4} placeholder="Enter your suggestions..." />
            </Form.Item>

            <Form.Item
              name="anonymize"
              valuePropName="checked" // Important to bind checkbox state correctly
            >
              <Checkbox>Keep me anonymous</Checkbox>
            </Form.Item>
          </>
        );
      })()}

      {(formType === "sample_storage" || formType === "phi_use") && (() => {
        return (
          <Form.Item
            name="radio_selection"
            label="Please choose one"
            rules={[{ required: true, message: "Please select an option" }]}
          >
            <Radio.Group>
              <Space direction="vertical">
                {form.fields.map((field, index) => (
                  <Radio key={field.value} value={field.name}>
                    {form.description[index]}
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          </Form.Item>
        )
      })()}

      {formType === "result_return" && (() => {
        return (
          <>
            {form.fields.map((field, index) => (
              <Form.Item
                key={field.name}
                name={field.name}
                label={field.label}
                rules={[{ required: true, message: "Please select an option" }]}
              >
                <Radio.Group>
                  <Space direction="vertical">
                    {field.options.map((option) => (
                      <Radio key={option.value} value={option.value}>
                        {option.label}
                      </Radio>
                    ))}
                  </Space>
                </Radio.Group>
              </Form.Item>
            ))}
          </>
        );
      })()}

      {formType === "num_children_enroll" && (() => {
        return (
          <>
            {form.fields.map((field, index) => (
              <Form.Item
                key={field.name}
                name={field.name}
                label={field.label}
                rules={[{ required: true, message: "Please select an option" }]}
              >
                <Radio.Group>
                  <Space direction="vertical">
                    {field.options.map((option) => (
                      <Radio key={option.value} value={option.value}>
                        {option.label}
                      </Radio>
                    ))}
                  </Space>
                </Radio.Group>
              </Form.Item>
            ))}
          </>
        );
      })()}

      {formType === "consent" && (() => {
        return (
          <>
            <div style={{ textAlign: "left", maxWidth: 700, margin: "0 auto 24px auto" }}>
              <Paragraph>
                {form.description.map((item, idx) => (
                  <div key={idx} style={{ marginBottom: 8 }}>
                    <strong>{idx + 1}.</strong> {item}
                  </div>
                ))}
              </Paragraph>
            </div>

            <Form.Item
              name={form.fields[0].name}
              label={form.fields[0].label}
              rules={[{ required: true, message: "Please enter your name" }]}
            >
              <Input.TextArea rows={1} placeholder="Enter your full name" />
            </Form.Item>

            <Form.Item
              name={form.fields[1].name}
              valuePropName="checked"
              rules={[{ required: true, message: "You must agree to continue" }]}
            >
              <Checkbox>
                {form.fields[1].label}
              </Checkbox>
            </Form.Item>
          </>
        );
      })()}

      {formType === "child_contact" && (
        <>
          {form.fields.map((field) => {
            const rules = [];
            if (field.required) {
              rules.push({required: true, message: "This field is required."})
            }

            if (field.pattern) {
              rules.push({
                pattern: new RegExp(field.pattern),
                message: "Invalid format",
              });
            }

            return (
              <Form.Item
                key={field.name}
                name={field.name}
                label={field.label}
                rules={rules}
              >
                {field.type === "input" && (
                  <Input type={field.input_type || "text"} placeholder={field.placeholder}/>
                )}

                {field.type === "select" && (
                  <Select placeholder="Select an option" options={field.options}/>
                )}
              </Form.Item>
            );
          })}
        </>
      )}

      <Form.Item style={{ textAlign: "center" }}>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};

export default ConsentFormSubmission;
