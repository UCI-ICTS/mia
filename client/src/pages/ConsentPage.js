// src/pages/ConsentPage.js

import "../style.css";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchConsentByInvite } from "../slices/consentSlice";
import { Button, Spin, Dropdown, Modal, Typography, Card } from "antd";
import { QuestionCircleOutlined } from "@ant-design/icons";

import ChatBubbles from "../components/ChatBubbles";
import FollowUpModal from "../components/FollowUpModal";

const { Title, Paragraph } = Typography;

// change this to 300000 for 5 minutes in production, 5000 in dev
const INACTIVITY_TIMEOUT_MS = 300000;

const ConsentPage = () => {
  const { session_slug } = useParams();
  const dispatch = useDispatch();

  const bottomRef = useRef(null);
  const topRef = useRef(null);

  const  [isInactive, setIsInactive] = useState(false);
  const timerRef = useRef(null);

  const [hasStarted, setHasStarted] = useState(false);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [countdown, setCountdown] = useState(10);
  const [contactModalVisible, setContactModalVisible] = useState(false);

  const { chat, consent, loading } = useSelector((state) => state.consentChat);
  const email = consent?.email || "Participant";

  /* -----------------------------
      FETCH SESSION ON LOAD
  ----------------------------- */
  useEffect(() => {
    if (session_slug) {
      dispatch(fetchConsentByInvite(session_slug));
    }
  }, [session_slug, dispatch]);

  useEffect(() => {
    // If user is on welcome screen → scroll top
  if (!hasStarted && topRef.current) {
    topRef.current.scrollIntoView({ behavior: "smooth" });
  }
}, [hasStarted]);

  /* -----------------------------
      INACTIVITY HANDLING
  ----------------------------- */
  
  const resetInactivityTimer = useCallback(() => {
    setIsInactive(false);
    if (timerRef.current) clearTimeout(timerRef.current);

    timerRef.current = setTimeout(() => {
      setIsInactive(true);
    }, INACTIVITY_TIMEOUT_MS);
  }, []);

    useEffect(() => {
    const activityEvents = ["mousemove", "keydown", "mousedown", "scroll", "touchstart"];

    const handleActivity = () => {
      // Only bother if chat has started
      if (hasStarted) {
        resetInactivityTimer();
      }
    };

    activityEvents.forEach((event) =>
      window.addEventListener(event, handleActivity)
    );

    // start timer when component mounts (in case user starts immediately)
    resetInactivityTimer();

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      activityEvents.forEach((event) =>
        window.removeEventListener(event, handleActivity)
      );
    };
  }, [resetInactivityTimer, hasStarted]);

  // when inactivity flips to true -> show modal ONCE
  useEffect(() => {
    if (isInactive && hasStarted && !showTimeoutModal) {
      setShowTimeoutModal(true);
      setCountdown(10);
    }
  }, [isInactive, hasStarted, showTimeoutModal]);

  // countdown logic
  useEffect(() => {
    if (!showTimeoutModal) return;
    if (countdown <= 0) {
      setHasStarted(false);
      setShowTimeoutModal(false);
      return;
    }
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [showTimeoutModal, countdown]);

  /* -----------------------------
      PAGE RENDER
  ----------------------------- */
  return (
    <div className="layout">
      {loading && <Spin size="large" className="card-icon" />}

      {/* HEADER */}
      <div className="chat-header">
        <div className="chat-header-left">
          <img
            src="/images/mia_logo.png"
            alt="Mia"
            style={{ height: 40, marginRight: 15 }}
          />
          <div>Mia by University of California, Irvine</div>
        </div>

        <Dropdown
          className="chat-header-right"
          placement="bottomRight"
          menu={{
            items: [
              {
                key: "faq",
                label: (
                  <a
                    href="https://gregorconsortium.org/learning"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    What is this study?
                  </a>
                ),
              },
              {
                key: "contact",
                label: <span onClick={() => setContactModalVisible(true)}>Contact the team</span>,
              },
              {
                key: "privacy",
                label: (
                  <a
                    href="https://research.uci.edu/human-research-protections/assessing-risks-and-benefits/privacy-and-confidentiality/protected-health-information-hipaa/"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Privacy and HIPAA Info
                  </a>
                ),
              },
            ],
          }}
        >
          <QuestionCircleOutlined className="help-button" />
        </Dropdown>
      </div>

      {/* BODY */}
      <div className="layout-dashboard" ref={topRef}>
        {!hasStarted ? (
          <Card className="chat-welcome" >
            <img
              src="/images/uci_health_logo.png"
              alt="UCI Health"
              style={{ width: 200, marginBottom: 20 }}
            />

            <Title level={3} className="card-title">Welcome</Title>

            <Paragraph className="card-label">
              We have some important information to share with you about the PMGRC study.
              Mia, our Medical Information Assistant, will walk you through it.
            </Paragraph>

            <Paragraph className="card-paragraph-italic">Chat takes 25–30 min</Paragraph>

            <Button
              onClick={() => {
                setHasStarted(true);
                setShowTimeoutModal(false);
                setCountdown(10);
                resetInactivityTimer(); // start inactivity tracking when user starts
              }}
              type="primary"
              className="login-form-button"
            >
              Start or resume
            </Button>
          </Card>
        ) : (
          <div className="chat-bubbles"> 
            {/* ChatBubbles handles ALL typing, delay, loading, render, animation */}
            <ChatBubbles
              chat={chat}
              username={email}
              session_slug={session_slug}
            />
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* CONTACT MODAL */}
      {consent?.email && (
        <FollowUpModal
          visible={contactModalVisible}
          onClose={() => setContactModalVisible(false)}
          userInfo={{ email: consent.email }}
        />
      )}

      {/* INACTIVITY MODAL */}
      <Modal
        className="uci-modal"
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
    </div>
  );
};

export default ConsentPage;
