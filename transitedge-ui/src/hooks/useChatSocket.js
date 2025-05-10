import { useEffect, useState } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:5001";

export function useChatSocket() {
  const [messages, setMessages] = useState([]);
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const newSocket = io(SOCKET_URL, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    newSocket.on("connect", () => {
      console.log("🟢 Connected to chat WebSocket");
      setConnected(true);
    });

    newSocket.on("disconnect", () => {
      console.log("🔴 Disconnected from chat WebSocket");
      setConnected(false);
    });

    newSocket.on("error", (error) => {
      console.error("❌ Socket error:", error);
    });

    newSocket.on("chat_message", (data) => {
      console.log("💬 Chat message received:", data);
      setMessages(prev => [...prev, data]);
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, []);

  const sendMessage = (message, sender = "Anonymous") => {
    if (socket && connected) {
      console.log("📤 Sending message:", { message, sender });
      socket.emit("chat_message", { message, sender });
    } else {
      console.warn("Cannot send message: socket not connected");
    }
  };

  return { messages, sendMessage, connected };
} 