// src/pages/ConsentPage.js
import React, { useEffect, useRef, useState } from "react";
import { Button, Dropdown, Input, Menu, Modal, Space, Typography } from "antd";
import { QuestionCircleOutlined, UserOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchConsentByInvite, submitConsentResponse } from "../slices/dataSlice";
import useInActivityTimer from "../components/InActivityTimer";
import ConsentFormSubmission from "../components/ConsentFormSubmission";
import FollowUpModal from "../components/FollowUpModal";
import { Bubble } from "@ant-design/x";

const { Title, Paragraph } = Typography;

const ConsentPage = () => {
  const { invite_id } = useParams();
  const dispatch = useDispatch();
  const { chat = [], consent, loading, error } = useSelector((state) => state.data);
  const lastMessage = chat[chat.length - 1];
  const lastNodeId = chat[chat.length - 1]?.node_id;
  const [contactModalVisible, setContactModalVisible] = useState(false);
  const isInactive = useInActivityTimer(5*60*1000)
  const [hasStarted, setHasStarted] = useState(false);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [countdown, setCountdown] = useState(10);
  const [visibleBotMessages, setVisibleBotMessages] = useState({});
  const bottomRef = useRef(null);

  // Automatically scroll to the bottom of chat
    useEffect(() => {
      const timer = setTimeout(() => {
        if (bottomRef.current) {
          bottomRef.current.scrollIntoView({ behavior: "smooth" });
        }
      }, 100); // small delay to allow render
    
      return () => clearTimeout(timer);
    }, [visibleBotMessages]);

  useEffect(() => {
    chat.forEach((entry, entryIndex) => {
      const botMsgs = entry?.bot_messages;
      if (botMsgs?.length > 0 && !visibleBotMessages[entry.node_id]) {
        botMsgs.forEach((_, msgIndex) => {
          setTimeout(() => {
            setVisibleBotMessages((prev) => {
              const current = prev[entry.node_id] || 0;
              return {
                ...prev,
                [entry.node_id]: Math.max(current, msgIndex + 1),
              };
            });
          }, msgIndex * 1500); // 1.5 seconds per message
        });
      }
    });  
  }, [chat])

  // Fetch consent on first load
  useEffect(() => {
    if (invite_id) {
      dispatch(fetchConsentByInvite(invite_id));
    }
  }, [dispatch, invite_id]);

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
  

  const handleResponseClick = (id) => {
    console.log("handleResponseClick", id)
    dispatch(submitConsentResponse({ invite_id, node_id: id }));
  };

  // console.log(hasStarted)

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
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
      
      <div style={{ flexGrow: 1, padding: "40px 20px", backgroundColor: "#f9f9f9" }}>
        {/* Start Page */}
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
          <div style={{ maxWidth: 800, margin: "0 auto" }}>
        {/* Main Content */}
            {chat.map((entry, index) => (
              <div key={index} style={{ marginBottom: 24 }}>
                {entry.echo_user_response && (  
                  <Bubble
                    header={<strong>{consent.email}</strong>}
                    placement="end"
                    shape="round"
                    avatar={{icon:<UserOutlined />}}
                    content={
                      <div style={{ fontFamily: "Georgia, serif", fontSize: 16 }}>
                        {entry.echo_user_response}
                      </div>
                    }
                  />
                )}
                {entry.bot_messages
                  ?.slice(0, visibleBotMessages[entry.node_id] || 0)
                  .map((msg, idx) => (
                    <Bubble
                      key={idx}
                      header={<strong>Mia</strong>}
                      placement="start"
                      shape="round"
                      content={
                        <div style={{ fontFamily: "Georgia, serif", fontSize: 16 }}>
                          <span dangerouslySetInnerHTML={{ __html: msg }} />
                        </div>
                      }
                      avatar={{ icon: <img src="/images/mia_logo.png" alt="Mia" /> }}
                    />
                ))}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

     {/* Button or Form */}
     {console.log(lastMessage)}
     {hasStarted &&
      lastMessage?.bot_messages?.length === (visibleBotMessages[lastNodeId] || 0) && (
        <div style={{ textAlign: "center", margin: "20px 0" }}>
          <div
            style={{
              display: "inline-flex",
              flexWrap: "wrap",
              justifyContent: "center",
            }}
          >
            {lastMessage?.user_render_type === "form" ? (
              <ConsentFormSubmission
                form={lastMessage?.user_responses}
                invite_id={invite_id}
              />
            ) : (
              lastMessage?.user_responses?.map(({ id, label }) => (
                <Button
                  key={id}
                  onClick={() => handleResponseClick(id)}
                  type="primary"
                  style={{ fontSize: 16, minWidth: 200, margin: 8 }}
                >
                  {label}
                </Button>
              ))              
            )}
          </div>
          <FollowUpModal
            visible={contactModalVisible}
            onClose={() => setContactModalVisible(false)}
            userInfo={{ email: consent.email }}
          />
          <Modal
            title="Are you still there?"
            visible={showTimeoutModal}
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
      )}
    </div>
  );
};

export default ConsentPage;