import { useState } from 'react';

export function Chat({ messages, sendMessage }) {
  const [newMessage, setNewMessage] = useState('');
  const [sender, setSender] = useState('Anonymous');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newMessage.trim()) {
      sendMessage(newMessage, sender);
      setNewMessage('');
    }
  };

  return (
    <div className="flex flex-col h-[500px] w-full max-w-2xl mx-auto bg-white rounded-lg shadow-lg">
      <div className="p-4 border-b">
        <h2 className="text-xl font-semibold">Chat</h2>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto">
        {messages.map((msg, index) => (
          <div key={index} className="mb-4">
            <div className="flex items-start">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-700">{msg.sender}</p>
                <p className="text-gray-800">{msg.message}</p>
                <p className="text-xs text-gray-500">
                  {new Date(msg.timestamp * 1000).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={sender}
            onChange={(e) => setSender(e.target.value)}
            placeholder="Your name"
            className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 text-white bg-blue-500 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
} 