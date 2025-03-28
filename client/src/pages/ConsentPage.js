// src/pages/ConsentPage.js
import React, { useEffect, useRef, useState } from "react";
import { Button, Dropdown, Input, Menu, Modal, Space, Typography } from "antd";
import { QuestionCircleOutlined, UserOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchConsentByInvite, submitConsentResponse } from "../slices/dataSlice";
import useInActivityTimer from "../components/InActivityTimer";
import CheckboxForm from "../components/CheckboxForm";
import FollowUpModal from "../components/FollowUpModal";
import { Bubble } from "@ant-design/x";

const { Title, Paragraph } = Typography;

const ConsentPage = () => {
  const { invite_id } = useParams();
  const dispatch = useDispatch();
  const { chat = [], consent, loading, error } = useSelector((state) => state.data);
  const lastMessage = chat[chat.length - 1]?.next_consent_sequence;
  const [contactModalVisible, setContactModalVisible] = useState(false);
  const isInactive = useInActivityTimer(5*60*1000)
  const [hasStarted, setHasStarted] = useState(false);
  const [showTimeoutModal, setShowTimeoutModal] = useState(false);
  const [countdown, setCountdown] = useState(10);
  const bottomRef = useRef(null);

  // Automatically scroll to the bottom of chat
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chat, hasStarted]);

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


   // Hook into injected form HTML
   useEffect(() => {
    const form = document.getElementById("checkbox-form");
    const submitButton = document.getElementById("submit-button");
  
    if (!form || !submitButton) return;
    
    const handleFormSubmit = (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const payload = Object.fromEntries(formData.entries());
      const node_id = payload["id_node"];
      delete payload["id_node"];
  
      dispatch(submitConsentResponse({ invite_id, node_id }));
    };
  
    const checkboxes = form.querySelectorAll("input[type='checkbox']");
    const updateSubmitState = () => {
      const anyChecked = Array.from(checkboxes).some((cb) => cb.checked);
      submitButton.disabled = !anyChecked;
    };
  
    form.addEventListener("submit", handleFormSubmit);
    checkboxes.forEach((cb) => cb.addEventListener("change", updateSubmitState));
  
    // Trigger once on mount in case some are pre-checked
    updateSubmitState();
  
    return () => {
      form.removeEventListener("submit", handleFormSubmit);
      checkboxes.forEach((cb) => cb.removeEventListener("change", updateSubmitState));
    };
  }, [chat]);
  

  const handleResponseClick = (id) => {
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
                    content={<span dangerouslySetInnerHTML={{ __html: entry.echo_user_response }} />}
                  />
                )}
                {entry.next_consent_sequence?.bot_messages?.map((msg, idx) => (  
                  <Bubble
                    header={<strong>Mia</strong>}
                    placement="start"
                    shape="round"
                    content={<span dangerouslySetInnerHTML={{ __html: msg }} />}
                    avatar={{icon:<img src="/images/mia_logo.png"/>}}
                  />
                ))}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

     {/* Button or Form */}
     {hasStarted && (
        <div style={{ textAlign: "center", margin: "20px 0" }}>
          <div
            style={{
              display: "inline-flex",
              flexWrap: "wrap",
              justifyContent: "center",
            }}
          >
            {lastMessage?.user_html_type === "form" ? (
            <div style={{ maxWidth: 600, margin: "0 auto", padding: 20 }}>
                <style>
                {`
                    #checkbox-form {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 12px;
                    margin-bottom: 16px;
                    }

                    .user-form-row {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    }

                    .user-form-row-label {
                    font-size: 16px;
                    }

                    #submit-button {
                    margin-top: 10px;
                    }
                `}
                </style>
                <div
                dangerouslySetInnerHTML={{
                    __html: lastMessage.user_responses?.[0]?.[1],
                }}
                />
            </div>
            ) : (
                lastMessage?.user_html_type === "form" ? (
                    <CheckboxForm nodeId={lastMessage.user_responses[0][0]} invite_id={invite_id} onSubmit={handleResponseClick} />
                  ) : (
                    lastMessage?.user_responses?.map(([id, label]) => (
                      <Button
                        key={id}
                        onClick={() => handleResponseClick(id)}
                        type="primary"
                        style={{ fontSize: 16, minWidth: 200, margin: 8 }}
                      >
                        {label}
                      </Button>
                    ))
                  )                  
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