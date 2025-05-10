// src/hooks/useRouteSocket.js
import { useEffect, useState } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:5001"; // or your deployed backend

export function useRouteSocket() {
  const [routeData, setRouteData] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    socket.on("connect", () => {
      console.log("🟢 Connected to /route WebSocket");
      setConnected(true);
      // Request initial route data
      socket.emit("get_route");
    });

    socket.on("disconnect", () => {
      console.log("🔴 Disconnected from /route WebSocket");
      setConnected(false);
    });

    socket.on("error", (error) => {
      console.error("❌ Socket error:", error);
    });

    socket.on("route", (data) => {
      console.log("📛 Route update received:", data);
      setRouteData(data);
    });

    // Request route updates every 30 seconds
    const interval = setInterval(() => {
      if (connected) {
        console.log("🔄 Requesting route update");
        socket.emit("get_route");
      }
    }, 30000);

    return () => {
      socket.disconnect();
      clearInterval(interval);
    };
  }, []);

  return { routeData, connected };
}
