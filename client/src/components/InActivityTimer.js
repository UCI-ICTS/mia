// src components/InActivityTimer.js

import { useEffect, useRef, useState } from "react";

const useInActivityTimer = (timeout = 300000) => {
  const [isInactive, setIsInactive] = useState(false);
  const timerRef = useRef(null);

  const resetTimer = () => {
    setIsInactive(false);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setIsInactive(true); // ⏰ Triggered after inactivity
    }, timeout);
  };

  useEffect(() => {
    const activityEvents = ["mousemove", "keydown", "mousedown", "scroll", "touchstart"];

    const handleActivity = () => resetTimer();

    activityEvents.forEach((event) =>
      window.addEventListener(event, handleActivity)
    );

    // Start the timer on mount
    resetTimer();

    return () => {
      clearTimeout(timerRef.current);
      activityEvents.forEach((event) =>
        window.removeEventListener(event, handleActivity)
      );
    };
  }, [timeout]);

  return isInactive;
};

export default useInActivityTimer;
