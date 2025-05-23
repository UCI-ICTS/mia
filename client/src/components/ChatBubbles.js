// src/components/ChatBubbles.js
import React from "react";
import { Typography, Row, Image } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { Bubble } from "@ant-design/x";
// import "../style.css";

const { Text } = Typography;

const ChatBubbles = ({ turn, username }) => {
  const { messages = [], render, echo_user_response = "" } = turn;

  return (
    <div className="bubble-container">
      {/* User responses */}
      {echo_user_response && typeof echo_user_response === "string" && (
        <Row justify="end" align="top">
          <Bubble
            header={<strong>{username}</strong>}
            placement="end"
            shape="round"
            avatar={{icon:<UserOutlined />}}
            content={
              <div style={{ fontFamily: "San Sarif, serif", fontSize: 16 }}>
                {echo_user_response}
              </div>
            }
          />
        </Row>
      )}
      {console.log(render.type, turn)}
      {/* Bot messages */}
      {render.type === "image" && (
        <div style={{ textAlign: "left", marginTop: 16 }}>
          <Image
            src={`/images/${render.content}`}
            alt="chat visual"
            preview={{ mask: <span>Click to zoom</span> }}
            style={{
              maxWidth: "100%",
              width: "400px",
              height: "auto",
              borderRadius: 8,
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)"
            }}
          />
        </div>
      )}
      
      {/* {Video Render from Bot} */}
      {render.type === "video" && (
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <div style={{ position: "relative", paddingBottom: "56.25%", height: 0, overflow: "hidden", borderRadius: 8, boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)" }}>
            <iframe
              src={render.content}
              title="Consent Video"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%"
              }}
            />
          </div>
        </div>
      )}
      {messages.map((msg, index) => (
        <Row key={`bot-${index}`} align="top">
          <Bubble
            key={index}
            header={<strong>Mia</strong>}
            placement="start"
            shape="round"
            content={
              <div style={{ fontFamily: "San Sarif, serif", fontSize: 16 }}>
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
