// src/components/AdminConsole.js

import { Card, Row, Col, Typography } from "antd";
import { UserOutlined, MessageOutlined, SolutionOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";

const { Title } = Typography;
const AdminConsole = () => {
  const dataState = useSelector((state) => state.data);

  const [data, setData] = useState({
    participant_count: dataState?.participants?.length || 0,
    participant_consent_complete_count: dataState?.participants?.filter(p => p.consent_complete)?.length || 0,
    consent_count: dataState?.scripts?.length || 0,
    participant_followup_count: dataState?.followUps?.filter(f => !f.resolved)?.length || 0,
  });

  // update counts when dataState changes
  useEffect(() => {
    setData({
      participant_count: dataState?.participants?.length || 0,
      participant_consent_complete_count: dataState?.participants?.filter(p => p.consent_complete)?.length || 0,
      consent_count: dataState?.scripts?.length || 0,
      participant_followup_count: dataState?.followUps?.filter(f => !f.resolved)?.length || 0,
    });
  }, [dataState]);


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
        {/* participants Card */}
        <Col xs={24} md={8}>
          <Card title="participants" bordered>
            <UserOutlined style={{ fontSize: "24px" }} />
            <p>Total participants: {data.participant_count}</p>
            <p>Consented participants: {data.participant_consent_complete_count}</p>
          </Card>
        </Col>

        {/* Scripted Consents Card */}
        <Col xs={24} md={8}>
          <Card title="Scripted Consents" bordered>
            <MessageOutlined style={{ fontSize: "24px" }} />
            <p>Script count: {data.consent_count}</p>
          </Card>
        </Col>

        {/* Follow Up Card */}
        <Col xs={24} md={8}>
          <Card title="Follow Up" bordered>
            <SolutionOutlined style={{ fontSize: "24px" }} />
            <p>Unresolved questions: {data.participant_followup_count}</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AdminConsole;
