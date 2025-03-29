// src/components/TypingBubble.js
import React, { useEffect, useState } from "react";
import { Bubble } from "@ant-design/x";

const TypingBubble = ({ message, avatar, delay = 30, header }) => {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    let currentChar = 0;
    const interval = setInterval(() => {
      if (currentChar < message.length) {
        setDisplayedText((prev) => prev + message[currentChar]);
        currentChar += 1;
      } else {
        clearInterval(interval);
      }
    }, delay);

    return () => clearInterval(interval);
  }, [message, delay]);

  return (
    <Bubble
      placement="start"
      shape="round"
      header={header}
      avatar={avatar}
      content={
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontSize: 16,
            whiteSpace: "pre-line",
          }}
          dangerouslySetInnerHTML={{ __html: displayedText }}
        />
      }
    />
  );
};

export default TypingBubble;
