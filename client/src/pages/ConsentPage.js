// src/pages/ConsentPage.js

import "../style.css";
import React, { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchConsentByInvite, submitConsentResponse } from "../slices/consentSlice";
import { Button, Spin, Alert, Dropdown, Modal, Space, Typography, Card } from "antd";
import { QuestionCircleOutlined } from "@ant-design/icons";
import ChatBubbles from "../components/ChatBubbles";
import ConsentFormSubmission from "../components/ConsentFormSubmission";
import useInActivityTimer from "../components/InActivityTimer";
import FollowUpModal from "../components/FollowUpModal";

const { Title, Paragraph } = Typography;

// helpers
const wait = (ms) => new Promise(res=> setTimeout(res, ms));
const typingDelay = (text) => 900 + Math.min(2000, text.length * 15);

const ConsentPage = () => {
  const { session_slug } = useParams();
  const dispatch = useDispatch();

  const bottomRef = useRef(null);
  const prevLenRef = useRef(0);        // tracks last rendered chat length
  const processingRef = useRef(false); // guard so page won't double-process a batch

  const isInactive = useInActivityTimer(5*60*1000)
  
  const [hasStarted, setHasStarted] = useState(false);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [countdown, setCountdown] = useState(10);
  const [isTyping, setIsTyping] = useState(false);
  
  // visible history & streaming state for current bot turn
  const [visibleTurns, setVisibleTurns] = useState([]);
  const [partialBotMessages, setPartialBotMessages] = useState([]);
  
  const [contactModalVisible, setContactModalVisible] = useState(false);

  const { chat, consent, session, loading, error } = useSelector((state) => state.consentChat);
  const email = consent ? consent.email : "Participant"
  
  // inactivity -> show modal once; don't re-trigger while open
  useEffect(() => {
    if (isInactive & !showTimeoutModal) {
      setShowTimeoutModal(true);
      setCountdown(10);
    }
  }, [isInactive, showTimeoutModal]);


  // inactivity countdown
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

  // scroll to bottom when content grows
  useEffect(() => {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: "smooth" });
  }, [visibleTurns, partialBotMessages, isTyping]);

  // initial fetch
  useEffect(() => {
    if (session_slug) {
      dispatch(fetchConsentByInvite(session_slug));
    }
  }, [session_slug, dispatch]);

  // scroll to bottom when content grows
  useEffect(() => {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: "smooth" });
  }, [visibleTurns, partialBotMessages, isTyping]);

  // INITIALIZE visibleTurns without delay (initial load or reload)
  useEffect(() => {
    if (!hasStarted || loading || !Array.isArray(chat)) return;
    // if we haven't initialized yet and we have chat, render instantly
    if (prevLenRef.current === 0 && chat.length > 0 && visibleTurns.length === 0) {
      setVisibleTurns(chat);
      prevLenRef.current = chat.length;
    }
  }, [hasStarted, loading, chat, visibleTurns.length]);

  // sequentially reveal newly appended turns (only after user actions)
  const revealNewTurns = useCallback(async (newTurns) => {
    processingRef.current = true;

    for (const turn of newTurns) {
      // always show user turns immediately
      if (turn.speaker !== "bot") {
        setVisibleTurns((prev) => [...prev, turn]);
        continue;
      }

      // bot turn: stream messages one-by-one with delays
      setIsTyping(true);
      setPartialBotMessages([]); // reset

      for (const msg of turn.messages) {
        // show a partial bubble growing as messages arrive
        setPartialBotMessages((prev) => [...prev, msg]);
        await wait(typingDelay(msg));
      }

      // commit the full turn to history, clear partial
      setVisibleTurns((prev) => [...prev, turn]);
      setPartialBotMessages([]);
      setIsTyping(false);
    }

    processingRef.current = false;
  }, []);

  // watch for new turns appended to chat AFTER initial
  useEffect(() => {
    if (!hasStarted || loading || !Array.isArray(chat)) return;
    const currentLen = chat.length;

    // nothing new
    if (currentLen <= prevLenRef.current) return;

    // first time (safety) — render all with no delay (handled above too)
    if (prevLenRef.current === 0 && visibleTurns.length === 0) {
      setVisibleTurns(chat);
      prevLenRef.current = currentLen;
      return;
    }

    // there's a new batch to reveal
    const batch = chat.slice(prevLenRef.current);
    prevLenRef.current = currentLen; // advance our pointer immediately

    if (!processingRef.current) {
      revealNewTurns(batch);
    } else {
      // in the unlikely case we're already processing, queue by re-running after finish
      const check = setInterval(() => {
        if (!processingRef.current) {
          clearInterval(check);
          revealNewTurns(batch);
        }
      }, 100);
      return () => clearInterval(check);
    }
  }, [chat, hasStarted, loading, revealNewTurns, visibleTurns.length]);

  const handleButtonClick = (node_id) => {
    // while typing, ignore clicks
    if (isTyping || partialBotMessages.length > 0) return;
    dispatch(submitConsentResponse({ session_slug, node_id }));
  };

  const renderFooter = () => {
    // hide footer while typing/streaming
    if (isTyping || partialBotMessages.length > 0) return null;
    if (!hasStarted || loading || visibleTurns.length === 0) return null;

    const lastTurn = visibleTurns[visibleTurns.length - 1];
    if (!lastTurn) return null;

    const { responses = [], node_id, end } = lastTurn;
    const isForm = typeof responses?.[0]?.label === "object" && "type" in responses[0].label;
    const hasResponses = Array.isArray(responses) && responses.length > 0;

    if (!hasResponses && !end) return null;
    
    return (
      <footer className="chat-footer">
      {isForm ? (
        <ConsentFormSubmission node_id={node_id} session_slug={session_slug} form={responses[0].label} />
      ) : (
        <div className="footer-button-container">
          {responses.map(({ id, label }) => (
            <Button
              key={id}
              onClick={() => handleButtonClick(id)}
              className="footer-button"
              disabled={isTyping}
            >
              {typeof label === "string" ? label : JSON.stringify(label)}
            </Button>
          ))}
        </div>
      )}
      {!isTyping && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>

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
    <div className="layout">
      {loading && <Spin size="large" className="card-icon" />}
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
          <QuestionCircleOutlined className="help-button" />
        </Dropdown>
      </div>
      <div className="layout-dashboard">
        {!hasStarted ? (
          <Card style={{ maxWidth: 600, margin: "0 auto", textAlign: "center" }}>
              <img
                src="/images/uci_health_logo.png"
                alt="UCI Health"
                style={{ width: 200, marginBottom: 20 }}
              />
              <Title level={3} className="card-title">Welcome</Title>
              <Paragraph className="card-label">
                We have some important information to share with you about the
                PMGRC study. Mia, our Medical Information Assistant, will walk
                you through it.
              </Paragraph>
              <Paragraph className="card-paragraph-italic">Chat takes 25–30 min</Paragraph>
              
              <div ref={bottomRef} />
              <Button
                onClick={() => {
                  setHasStarted(true);
                  setShowTimeoutModal(false);
                  setCountdown(10);
                }}
                type="primary"
                className="login-form-button"
              >Start or resume</Button>
            </Card>
        ) : (
          <div >
            {chat.map((turn, idx) => (
              <ChatBubbles key={idx} turn={turn} username={email}/>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
      {consent?.email && (
        <FollowUpModal
          visible={contactModalVisible}
          onClose={() => setContactModalVisible(false)}
          userInfo={{ email: consent.email }}
        />
      )}
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

      {renderFooter()}

    </div>
  );
};

export default ConsentPage;
