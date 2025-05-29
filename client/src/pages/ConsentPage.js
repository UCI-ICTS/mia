// src/pages/ConsentPage.js

import React, { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchConsentByInvite, submitConsentResponse } from "../slices/consentSlice";
import { Button, Spin, Alert, Dropdown, Modal, Space, Typography } from "antd";
import { QuestionCircleOutlined } from "@ant-design/icons";
import ChatBubbles from "../components/ChatBubbles";
import ConsentFormSubmission from "../components/ConsentFormSubmission";
import useInActivityTimer from "../components/InActivityTimer";
import FollowUpModal from "../components/FollowUpModal";

const { Title, Paragraph } = Typography;

const ConsentPage = () => {
  const { invite_id } = useParams();
  const dispatch = useDispatch();
  const bottomRef = useRef(null);
  const isInactive = useInActivityTimer(5*60*1000)
  const [hasStarted, setHasStarted] = useState(false);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [countdown, setCountdown] = useState(10);
  const [isTyping, setIsTyping] = useState(false);
  const [contactModalVisible, setContactModalVisible] = useState(false);

  const { chat, consent, session, loading, error } = useSelector((state) => state.consentChat);
  const email = consent ? consent.email : "Participant"
  // Inactivity timer
  useEffect(() => {
    if (isInactive) {
      setShowTimeoutModal(true);
      setCountdown(10);
    }
  }, [isInactive]);

  useEffect(() => {
    let timer;
    if (showTimeoutModal && countdown > 0) {
      timer = setTimeout(() => {
        setCountdown((prev) => prev - 1);
      }, 1000);
    } else if (countdown === 0) {
      // Trigger lockout here
      setHasStarted(false);
      setShowTimeoutModal(false);
      console.log("User session locked due to inactivity.");
      // Optionally show another modal or redirect
    }

    return () => clearTimeout(timer);
  }, [showTimeoutModal, countdown]);

  // Automatically scroll to bottom when chat updates
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chat]);

  useEffect(() => {
    if (invite_id) {
      dispatch(fetchConsentByInvite(invite_id));
    }
  }, [invite_id, dispatch]);

  const handleButtonClick = (node_id) => {
    dispatch(submitConsentResponse({ invite_id, node_id }));
  };

  const renderFooter = () => {
    if (!chat || chat.length === 0 || loading || !hasStarted) return null;

    const lastTurn = chat[chat.length - 1];
    const { responses = [], render = {}, node_id, end} = lastTurn;
    const isForm = typeof responses?.[0]?.label === "object" && "type" in responses[0].label;
    const hasResponses = Array.isArray(responses) && responses.length > 0;
    
    return (
      <footer
        style={{
          padding: "20px",
          backgroundColor: "#fff",
          borderTop: "1px solid #ddd",
          position: "sticky",
          bottom: 0,
          width: "100%",
          textAlign: "center",
          zIndex: 1000,
        }}
      >
      {!isTyping && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          {isForm ? (
            <ConsentFormSubmission node_id={node_id} invite_id={invite_id} form={responses[0].label} />
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center" }}>
              {responses.map(({ id, label }) => (
                <Button
                  key={id}
                  onClick={() => handleButtonClick(id)}
                  type="primary"
                  style={{ fontSize: 16, minWidth: 200, margin: 8 }}
                >
                  {typeof label === "string" ? label : JSON.stringify(label)}
                </Button>
              ))}
            </div>
          )}

          {end && (
            <div style={{ textAlign: "center", marginTop: 24 }}>
              <Button
                type="primary"
                onClick={() => {
                  if (window.opener) {
                    window.close();
                  } else {
                    window.location.href = "https://gregorconsortium.org/learning";
                  }
                }}
                style={{ minWidth: 200 }}
              >
                Finish & Close
              </Button>
            </div>
          )}
        </div>
      )}
    </footer>
    )
  };

  return (
    <div style={{maxHeight: "100vh", overflowY: "auto" }}>
      {loading && <Spin size="large" style={{ marginBottom: 24 }} />}
      {/* Header */}
      <div
        style={{
          position: "sticky",
          top: 0,
          zIndex: 1000,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between", // this spreads left and right
          padding: "12px 20px",
          borderBottom: "1px solid #ccc",
          backgroundColor: "#fff",
        }}
      >
        {/* Left side: Logo and title */}
        <div style={{ display: "flex", alignItems: "center" }}>
          <img
            src="/images/mia_logo.png"
            alt="Mia"
            style={{ height: 40, marginRight: 15 }}
          />
          <div>Mia by University of California, Irvine</div>
        </div>

        {/* Right side: Help dropdown */}
        <Dropdown
          placement="bottomRight"
          menu={{
            items: [
              { key: "faq", label: (
                <a
                  href="https://gregorconsortium.org/learning"
                  target="_blank"
                  rel="noopener noreferrer"
                >What is this study?</a>
              )},
              {
                key: "contact",
                label: (
                  <span onClick={() => setContactModalVisible(true)}>
                    Contact the team
                  </span>
                ),
              },
              { key: "privacy", label:(
              <a
                href="https://research.uci.edu/human-research-protections/assessing-risks-and-benefits/privacy-and-confidentiality/protected-health-information-hipaa/"
                tartget="_blank"
                rel="noopener noreferrer"
              >Privacy and HIPAA Info</a>
             )},
            ],
          }}
        >
          <QuestionCircleOutlined style={{ fontSize: 20, cursor: "pointer" }} />
        </Dropdown>
      </div>

      {!hasStarted ? (
        <div style={{ maxWidth: 600, margin: "0 auto", textAlign: "center" }}>
            <img
              src="/images/uci_health_logo.png"
              alt="UCI Health"
              style={{ width: 200, marginBottom: 20 }}
            />
            <Title level={3}>Welcome</Title>
            <Paragraph>
              We have some important information to share with you about the
              PMGRC study. Mia, our Medical Information Assistant, will walk
              you through it.
            </Paragraph>
            <Paragraph>Chat takes 25–30 min</Paragraph>
            <img
              src="/images/hipaa_compliant.png"
              alt="HIPAA Compliant"
              style={{ width: 150, marginTop: 20 }}
            />
            <div ref={bottomRef} />
            <Button
              onClick={() => {
                setHasStarted(true);
                setShowTimeoutModal(false);
                setCountdown(10);
              }}
              type="primary"
              style={{ fontSize: 16, minWidth: 200, margin: 8 }}
            >Start or resume</Button>
          </div>
      ) : (
        <div style={{ marginBottom: 100 }}>
          {chat.map((turn, idx) => (
            <ChatBubbles key={idx} turn={turn} username={email}/>
          ))}
          <div ref={bottomRef} />
        </div>
      )}

      {consent?.email && (
        <FollowUpModal
          visible={contactModalVisible}
          onClose={() => setContactModalVisible(false)}
          userInfo={{ email: consent.email }}
        />
      )}
      <Modal
        title="Are you still there?"
        open={showTimeoutModal}
        closable={false}
        footer={null}
        centered
      >
        <p>You’ve been inactive. Locking the session in {countdown} seconds...</p>
        <Button
          type="primary"
          onClick={() => {
            setShowTimeoutModal(false);
            setCountdown(10);
          }}
        >
          I’m still here
        </Button>
      </Modal>

      {renderFooter()}

    </div>
  );
};

export default ConsentPage;
