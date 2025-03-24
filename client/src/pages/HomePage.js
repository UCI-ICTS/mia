// src/pages/HomePage.js

import { Layout, Row, Col, Typography, Image, Card } from "antd";
import { Link } from "react-router-dom";

const { Header, Content } = Layout;
const { Title, Paragraph } = Typography;

const HomePage = () => {
  return (
    <Layout style={{ width: "100%", margin: "0", padding: "0" }}>
      {/* Navbar */}
      <Header style={{ background: "#1565c0", padding: "15px 20px", textAlign: "right" }}>
        <Link to="/login" style={{ color: "white", fontSize: "16px", textDecoration: "none" }}>
          Staff Login
        </Link>
      </Header>

      {/* Hero Section */}
      <Content style={{ background: "#1565c0", padding: "60px 0" }}>
        <Row justify="center" align="middle" style={{ maxWidth: "1200px", margin: "0 auto", padding: "0 20px" }}>
          <Col xs={24} md={12} style={{ textAlign: "left" }}>
            <Title level={1} style={{ color: "white", fontSize: "40px", fontWeight: "bold" }}>
              Meet Mia
            </Title>
            <Paragraph style={{ color: "white", fontSize: "18px", maxWidth: "500px" }}>
              Our virtual Medical Information Assistant (Mia)
            </Paragraph>
            <Paragraph style={{ color: "white", fontSize: "18px", maxWidth: "500px" }}>
              A HIPAA-compliant clinical consentbot that facilitates virtual conversations with patients.
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
      <Content style={{ padding: "50px 20px", background: "#f8f9fa" }}>
        <Title level={3} style={{ textAlign: "center", fontSize: "28px", fontWeight: "bold" }}>
          Offering medical assistance is simple with Mia
        </Title>
        <Row gutter={[24, 24]} justify="center">
          {[
            { title: "1. Share Mia", text: "Provide a link to your patients prior to their appointment.", italic: "Available for patients and clinicians in the US." },
            { title: "2. Intake", text: "Via virtual consent, Mia gathers intake information, including personal and medical history." },
            { title: "3. Education", text: "Mia guides your patients through pre-appointment education from home." },
            { title: "4. Guidance", text: "Clinicians receive a summary note and notifications about patient eligibility." },
            { title: "5. Ordering", text: "The order form auto-fills with patient data, allowing quick service selection." },
            { title: "6. Results", text: "Patients receive results, and clinicians can follow up or automate next steps." },
          ].map((item, index) => (
            <Col xs={24} md={12} key={index}>
              <Card style={{ background: "#f0f2f5", padding: "20px", borderRadius: "10px", textAlign: "left" }}>
                <Title level={5} style={{ fontWeight: "bold", marginBottom: "10px" }}>{item.title}</Title>
                <Paragraph style={{ fontSize: "16px" }}>{item.text}</Paragraph>
                {item.italic && <Paragraph style={{ fontSize: "14px", fontStyle: "italic", color: "#555" }}>{item.italic}</Paragraph>}
              </Card>
            </Col>
          ))}
        </Row>
      </Content>
    </Layout>
  );
};

export default HomePage;
