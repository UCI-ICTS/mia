// src/components/SummaryConsole.js

import "../style.css";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { Card, Row, Col, Typography } from "antd";
import { UserOutlined, MessageOutlined, SolutionOutlined } from "@ant-design/icons";

const { Title } = Typography;
const SummaryConsole = () => {
  const navigate = useNavigate();
  const dataState = useSelector((state) => state.data);

  const [data, setData] = useState({
    participant_count: dataState?.participants?.length || 0,
    participant_consent_complete_count: dataState?.participants?.filter(p => p.consent_complete)?.length || 0,
    consent_count: dataState?.scripts?.length || 0,
    participant_followup_count: dataState?.followUps?.filter(f => !f.resolved)?.length || 0,
  });

  // Update counts when dataState changes
  useEffect(() => {
    setData({
      participant_count: dataState?.participants?.length || 0,
      participant_consent_complete_count: (dataState?.participants || []).filter(p => p.consent_complete)?.length || 0,
      consent_count: dataState?.scripts?.length || 0,
      participant_followup_count: (dataState?.followUps || []).filter(f => !f.resolved)?.length || 0,
    });
  }, [dataState]);

  return (
    <div className="layout">
      <div className="primary-header">
        <Title level={3} className="primary-title">Summary Console</Title>
      </div>
      <hr />
      <Row gutter={[16, 16]}>
        {/* participants Card */}
        <Col xs={24} md={8}>
          <Card 
            title={<div className="card-title">Participants</div>} 
            className="primary-card"
            onClick={()=> navigate("/dashboard/participants")}
          >
            <UserOutlined className="card-icon" />
            <p className="card-label">Total participants: {data.participant_count}</p>
            <p className="card-label">Consented participants: {data.participant_consent_complete_count}</p>
          </Card>
        </Col>

        {/* Scripted Consents Card */}
        <Col xs={24} md={8}>
          <Card 
            title={<div className="card-title">Chat Graphs</div>}
            className="primary-card"
            onClick={()=> navigate("/dashboard/scripts")}
          >
            <MessageOutlined className="card-icon"/>
            <p className="card-label">Script count: {data.consent_count}</p>
          </Card>
        </Col>

        {/* Follow Up Card */}
        <Col xs={24} md={8}>
          <Card
            title={<div className="card-title">Follow Up</div>}
            className="primary-card"
            onClick={()=> navigate("/dashboard/follow_up")}
          >
            <SolutionOutlined className="card-icon"/>
            <p className="card-label">Unresolved questions: {data.participant_followup_count}</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SummaryConsole;
