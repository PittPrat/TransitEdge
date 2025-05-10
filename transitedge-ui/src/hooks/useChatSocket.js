import { useEffect, useState } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:5001";

export function useChatSocket() {
  const [messages, setMessages] = useState([]);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const newSocket = io(SOCKET_URL);
    setSocket(newSocket);

    newSocket.on("connect", () => {
      console.log("🟢 Connected to chat WebSocket");
    });

    newSocket.on("chat_message", (data) => {
      console.log("💬 Chat message received:", data);
      setMessages(prev => [...prev, data]);
    });

    return () => {
      newSocket.disconnect();
    };
  }, []);

  const sendMessage = (message, sender = "Anonymous") => {
    if (socket) {
      socket.emit("chat_message", { message, sender });
    }
  };

  return { messages, sendMessage };
} 