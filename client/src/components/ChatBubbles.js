import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Button, Image, Row } from "antd";
import { Bubble } from "@ant-design/x";
import { UserOutlined } from "@ant-design/icons";
import TypingBubble from "./TypingBubble";
import { submitConsentResponse } from "../slices/consentSlice";
import ConsentFormSubmission from "../components/ConsentFormSubmission";
import "../style.css";

const wait = (ms) => new Promise((res) => setTimeout(res, ms));
// const typingDelay = (msg) => 900 + Math.min(2000, msg.length * 15);
const typingDelay = (msg) => 10;


const ChatBubbles = ({ chat = [], username, session_slug }) => {
  const dispatch = useDispatch()
  const bottomRef = useRef(null);
  const prevLenRef = useRef(0);
  const [visibleTurns, setVisibleTurns] = useState([]);
  const [partialBotMessages, setPartialBotMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  // Scroll on update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [visibleTurns, partialBotMessages, isTyping]);

  // Initial render
  useEffect(() => {
    if (prevLenRef.current === 0 && chat.length > 0 && visibleTurns.length === 0) {
      setVisibleTurns(chat);
      prevLenRef.current = chat.length;
    }
  }, [chat, visibleTurns.length]);

  // Detect and reveal new turns
  useEffect(() => {
    const currentLen = chat.length;
    if (currentLen <= prevLenRef.current) return;

    const newTurns = chat.slice(prevLenRef.current);
    prevLenRef.current = currentLen;

    const reveal = async () => {
      for (const turn of newTurns) {
        if (turn.speaker !== "bot") {
          setVisibleTurns((prev) => [...prev, turn]);
          continue;
        }

        setIsTyping(true);
        setPartialBotMessages([]);
        for (const msg of turn.messages) {
          setPartialBotMessages((prev) => [...prev, msg]);
          await wait(typingDelay(msg));
        }
        setVisibleTurns((prev) => [...prev, turn]);
        setPartialBotMessages([]);
        setIsTyping(false);
      }
    };
    reveal();
  }, [chat]);

  /* -----------------------------
      FOOTER BUTTON RENDER
  ----------------------------- */
  const renderFooter = () => {
    if (isTyping ||  !chat || chat.length === 0) return null;
    const lastTurn = chat[chat.length - 1];
    if (!lastTurn) return null;

    const { responses = [], node_id, end } = lastTurn;
    const isForm =
      typeof responses?.[0]?.label === "object" &&
      responses[0]?.label?.type;

    return (
      <footer className="chat-footer">
        {isForm ? (
          <ConsentFormSubmission
            node_id={node_id}
            session_slug={session_slug}
            form={responses[0].label}
          />
        ) : (
          <div className="footer-button-container">
            {responses.map(({ id, label }) => (
              <Button
                key={id}
                className="footer-button"
                onClick={() =>
                  dispatch(submitConsentResponse({ session_slug, node_id: id }))
                }
              >
                {typeof label === "string" ? label : JSON.stringify(label)}
              </Button>
            ))}
          </div>
        )}

        {end && (
          <div style={{ marginTop: 24 }}>
            <Button
              type="primary"
              onClick={() => {
                if (window.opener) window.close();
                else window.location.href = "https://gregorconsortium.org/learning";
              }}
              style={{ minWidth: 200 }}
            >
              Finish & Close
            </Button>
          </div>
        )}
      </footer>
    );
  };

  return (
    <div className="bubble-container">
      {visibleTurns.map((turn, idx) => (
        <React.Fragment key={idx}>
          
          {turn.speaker === "bot" ? (
            turn.messages.map((msg, index) => (
              <Row key={`bot-${idx}-${index}`} className="bubble-row-left">
                <Bubble
                  className="bot-bubble"
                  header={<strong className="card-label">Mia</strong>}
                  placement="start"
                  shape="round"
                  content={<span dangerouslySetInnerHTML={{ __html: msg }} />}
                  avatar={{ src: "/images/mia_logo.png" }}
                />
              </Row>
            ))
          ) : (
            turn.messages.map((msg, index) => (
              <Row key={`usr-${idx}-${index}`} className="bubble-row-right">
                <Bubble
                  className="user-bubble"
                  header={<strong className="card-label">{username}</strong>}
                  placement="end"
                  shape="round"
                  content={<div>{msg}</div>}
                  avatar={{ icon: <UserOutlined /> }}
                />
              </Row>
            ))
          )}
          {console.log(turn.render?.type)}
          {turn.render?.type === "image" && (
            <img
              className="chat-image"
              src={`/images/${turn.render.content}`}
              alt={turn.render.content}
            />
          )}
          {turn.render?.type === "video" && (
            <iframe
              className="chat-video"
              src={turn.render.content}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          )}
        </React.Fragment>
      ))}

      {/* Streaming messages */}
      {partialBotMessages.length > 0 &&
        partialBotMessages.map((msg, index) => (
          <Row key={`typing-${index}`} className="bubble-row-left">
            <Bubble
              className="bot-bubble"
              header={<strong className="card-label">Mia</strong>}
              placement="start"
              shape="round"
              content={<span dangerouslySetInnerHTML={{ __html: msg }} />}
              avatar={{ src: "/images/mia_logo.png" }}
            />
          </Row>
        ))}

      {/* Typing indicator */}
      {isTyping && <TypingBubble />}
      {renderFooter()}
      <div ref={bottomRef} />
    </div>
  );
};

export default ChatBubbles;
