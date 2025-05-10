// src/hooks/useRouteSocket.js
import { useEffect, useState } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:5001"; // or your deployed backend

export function useRouteSocket() {
  const [routeData, setRouteData] = useState(null);

  useEffect(() => {
    const socket = io(SOCKET_URL);

    socket.on("connect", () => {
      console.log("🟢 Connected to /route WebSocket");
    });

    socket.on("route", (data) => {
      console.log("📡 Route update received:", data);
      setRouteData(data);
    });

    // Optionally emit every 30 seconds
    const interval = setInterval(() => {
      socket.emit("get_route");
    }, 30000);

    return () => {
      socket.disconnect();
      clearInterval(interval);
    };
  }, []);

  return routeData;
}
