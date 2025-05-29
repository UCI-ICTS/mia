// src/components/ChatBubbles.js
import React from "react";
import { Typography, Row, Image } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { Bubble } from "@ant-design/x";
// import "../style.css";

const { Text } = Typography;

const ChatBubbles = ({ turn, username }) => {
  const {messages } = turn;
  console.log(turn.messages)
  return (
    <div className="bubble-container">
    
    {/* Text Bot messages */}
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
  );
};

export default ChatBubbles;
