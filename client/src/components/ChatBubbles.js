// src/components/ChatBubbles.js

import { Typography, Row, Image } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { Bubble } from "@ant-design/x";
import "../style.css";

const { Text } = Typography;

const ChatBubbles = ({ turn, username }) => {
  const { messages = [], speaker, render } = turn || {};
  const isImage = render?.type === "image" && render?.content;
  const isVideo = render?.type === "video" && render?.content;

  return (
    <div className="bubble-container">
      {speaker === "bot" ? (
        <div >
          {messages.map((msg, index) => (
            <Row key={`bot-${index}`} className="bubble-row-left">
              <Bubble
                key={index}
                className="bot-bubble"
                header={<strong className="card-label">Mia</strong>}
                placement="start"
                shape="round"
                content={
                  <div >
                    <span dangerouslySetInnerHTML={{ __html: msg }} />
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
            <Row key={`usr-${index}`} className="bubble-row-right">
              <Bubble
                className="user-bubble"
                header={<strong className="card-label">{username}</strong>}
                placement="end"
                shape="round"
                avatar={{icon:<UserOutlined />}}
                content={
                  <div >
                    {msg}
                  </div>
                }
              />
            </Row>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatBubbles;
