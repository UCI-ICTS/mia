import React from "react";
import { Bubble } from "@ant-design/x";

const TypingBubble = () => (
  <Bubble
    loading
    className="bot-bubble"
    header={<strong className="card-label">Mia</strong>}
    placement="start"
    shape="round"
    avatar={{ src: "/images/mia_logo.png" }}
  />
);

export default TypingBubble;
