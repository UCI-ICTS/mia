// src/components/ChatBubbles.js
import React from "react";
import { Typography, Row, Image } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { Bubble } from "@ant-design/x";
// import "../style.css";

const { Text } = Typography;

const ChatBubbles = ({ turn, username }) => {
  const {messages, speaker } = turn;
  return (
    <div className="bubble-container">
      {speaker === "bot" ? (
        <div>
          {messages.map((msg, index) => (
            <Row key={`bot-${index}`} align="top">
              <Bubble
                key={index}
                header={<strong>Mia</strong>}
                placement="start"
                shape="round"
                content={
                  <div style={{ fontFamily: "sans-serif", fontSize: 16 }}>
                    <span dangerouslySetInnerHTML={{ __html: msg }} />
                    {/* <div ref={bottomRef} /> */}
                  </div>
                }
                avatar={{ icon: <img src="/images/mia_logo.png" alt="Mia" /> }}
              />
            </Row>
          ))}
        </div>
      ) : (
        <div>
          {messages.map((msg, index) => (
            <Row justify="end" align="top">
              <Bubble
                header={<strong>{username}</strong>}
                placement="end"
                shape="round"
                avatar={{icon:<UserOutlined />}}
                content={
                  <div style={{ fontFamily: "sans-serif", fontSize: 16 }}>
                    {msg}
                  </div>
                }
              />
            </Row>
          ))}
      </div>
      )}
    {/* Text Bot messages */}
      

    </div>
  );
};

export default ChatBubbles;
