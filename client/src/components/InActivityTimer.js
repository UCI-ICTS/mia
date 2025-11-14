// src components/InActivityTimer.js

import { useEffect, useRef, useState } from "react";

const useInActivityTimer = (timeout = 300000) => {
  const [isInactive, setIsInactive] = useState(false);
  const timerRef = useRef(null);

  const resetTimer = () => {
    setIsInactive(false);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setIsInactive(true);
    }, timeout);
  };

  useEffect(() => {
    const activityEvents = ["mousemove", "keydown", "mousedown", "scroll", "touchstart"];

    const handleActivity = () => resetTimer();

    activityEvents.forEach((event) => window.addEventListener(event, handleActivity));

    resetTimer(); // start timer on mount

    return () => {
      clearTimeout(timerRef.current);
      activityEvents.forEach((event) => window.removeEventListener(event, handleActivity));
    };
  }, [timeout]);

  return { isInactive, reset: resetTimer };
};

export default useInActivityTimer;
