import React from "react";
import { Bubble } from "@ant-design/x";

const TypingBubble = () => (
  <Bubble
    loading
    className="bot-bubble"
    header={<strong className="card-label">Kauro</strong>}
    placement="start"
    shape="round"
    avatar={{ src: "/doctor_robot.svg" }}
  />
);

export default TypingBubble;
