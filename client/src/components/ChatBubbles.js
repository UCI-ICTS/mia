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
        <div>
          {/* Optional media block */}
          {isImage && (
            <Row key={`bot-media-${render.content}`} className="bubble-row-left">
              {/* Use Ant Image for better loading/resize (no preview) */}
              <Image
                src={`/images/${render.content}`}
                alt="Mia illustration"
                className="bubble-row-image"
                preview={false}
              />
            </Row>
          )}

          {isVideo && (
            <Row key={`bot-media-${render.content}`} className="bubble-row-left">
              {/* Use Ant Image for better loading/resize (no preview) */}
              <div className="bubble-row-video">
                <iframe
                  src={render.content}
                  title="Mia video"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            </Row>
          )}

          {/* Text bubbles */}
          {messages.map((msg, index) => (
            <Row key={`bot-${index}`} className="bubble-row-left">
              <Bubble
                className="bot-bubble"
                header={<strong className="card-label">Mia</strong>}
                placement="start"
                shape="round"
                content={<span dangerouslySetInnerHTML={{ __html: msg }} />}
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
                header={username}
                placement="end"
                shape="round"
                avatar={{ icon: <UserOutlined /> }}
                content={<div>{msg}</div>}
              />
            </Row>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatBubbles;
