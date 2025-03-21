// src/components/AdminConsole.js

import { Card, Row, Col, Typography } from "antd";
import { UserOutlined, MessageOutlined, SolutionOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import axios from "axios";

const { Title } = Typography;

const AdminConsole = () => {
  const [data, setData] = useState({
    user_count: 0,
    user_consent_complete_count: 0,
    chat_count: 0,
    user_followup_count: 0,
  });

  useEffect(() => {
    axios.get("/api/admin-stats") // Update with correct API endpoint
      .then(response => setData(response.data))
      .catch(error => console.error("Error fetching admin stats:", error));
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <Title level={3}>Admin Console</Title>
      <hr />
      <Row gutter={[16, 16]}>
        {/* Users Card */}
        <Col xs={24} md={8}>
          <Card title="Users" bordered>
            <UserOutlined style={{ fontSize: "24px" }} />
            <p>Total users: {data.user_count}</p>
            <p>Consented users: {data.user_consent_complete_count}</p>
          </Card>
        </Col>

        {/* Scripted Chats Card */}
        <Col xs={24} md={8}>
          <Card title="Scripted Chats" bordered>
            <MessageOutlined style={{ fontSize: "24px" }} />
            <p>Script count: {data.chat_count}</p>
          </Card>
        </Col>

        {/* Follow Up Card */}
        <Col xs={24} md={8}>
          <Card title="Follow Up" bordered>
            <SolutionOutlined style={{ fontSize: "24px" }} />
            <p>Unresolved questions: {data.user_followup_count}</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AdminConsole;
