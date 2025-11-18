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
              src="/doctor_robot.svg"
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
            title: "1. Share Mia", 
            text: "Provide a link to your participants prior to their appointment.",
            // italic: "Available for patients and clinicians in the US." 
          }, { 
            title: "2. Enrollment", 
            text: "Join the study." 
          }, { 
            title: "3. Education",
            text: "Mia guides your patients through pre-appointment education from home."
          }, { 
            title: "4. Guidance",
            text: "Clinicians receive a summary note and notifications about patient eligibility."
          }, {
            title: "5. Ordering",
            text: "The order form auto-fills with patient data, allowing quick service selection."
          }, {
            title: "6. Results", 
            text: "Patients receive results, and clinicians can follow up or automate next steps."
          },
          ].map((item, index) => (
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
