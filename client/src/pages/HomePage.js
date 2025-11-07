// src/pages/HomePage.js

import "../style.css"
import { Layout, Row, Col, Typography, Image, Card } from "antd";
import { Link } from "react-router-dom";

const { Header, Content } = Layout;
const { Title, Paragraph } = Typography;

const HomePage = () => {
  return (
    <Layout className="layout">
      {/* Navbar */}
      <Header className="home-header">
        <Link to="/login" className="custom-link">
          Staff Login
        </Link>
      </Header>

      {/* top content section */}
      <Content className="home-top-content">
        <Row justify="center" align="middle" style={{ maxWidth: "1200px", margin: "0 auto", padding: "0 20px" }}>
          <Col xs={24} md={12} >
            <Title level={1} className="home-title">
              Meet Mia
            </Title>
            <Paragraph className="home-paragraph">
              Our virtual Medical Information Assistant (Mia)
            </Paragraph>
            
          </Col>
          <Col xs={24} md={12} style={{ textAlign: "right" }}>
            <Image 
              src="/images/mia_logo.png"
              alt="Mia Logo"
              width={180} 
              style={{ borderRadius: "50%" }}
              preview={false}
            />
          </Col>
        </Row>
      </Content>

      {/* Steps Section */}
      <Content className="home-bottom-content">
        <Title level={3} className="home-subtitle">
          A clinical chatbot that facilitates conversations with patients.
        </Title>
        <Row gutter={[24, 24]} justify="center">
          {[{ 
            title: "1. Easy Invitations", 
            text: "MIA emails participants a secure link to begin their consent session.",
            italic: "No downloads, no confusion — just click and start."
          }, { 
            title: "2. Family Enrollment",
            text: "Participants can invite family members directly during their session.",
            italic: "Enrollment expands without extra staff work."
          }, { 
            title: "3. Built-In Knowledge Checks",
            text: "MIA guides participants through pre-approved comprehension quizzes.",
            italic: "Ensures understanding before consent is finalized."
          }, { 
            title: "4. Full Audit Trail",
            text: "Every interaction is logged with timestamps and script versioning.",
            italic: "Compliance and reproducibility built in."
          }, {
            title: "5. Streamlined Workflows",
            text: "Forms auto-fill with participant data across steps.",
            italic: "Reduces repetitive entry and saves staff time."
          }, {
            title: "6. Integrated Results",
            text: "Consent outcomes and test results flow back to clinicians.",
            italic: "Follow-up can be automated or handled directly."
          }].map((item, index) => (
            <Col xs={24} md={12} key={index}>
              <Card className="home-card">
                <Title level={5} className="home-card-title">{item.title}</Title>
                <Paragraph className="card-paragraph">{item.text}</Paragraph>
                {item.italic && <Paragraph className="card-paragraph-italic"
                >{item.italic}</Paragraph>}
              </Card>
            </Col>
          ))}
        </Row>
      </Content>
    </Layout>
  );
};

export default HomePage;
