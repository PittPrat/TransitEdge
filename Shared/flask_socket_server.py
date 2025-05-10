from flask import Flask
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow frontend connection

@app.route("/")
def index():
    return "SocketIO server is running!"

@socketio.on("connect")
def handle_connect():
    print("🟢 Client connected")

@socketio.on("get_route")
def handle_get_route():
    print("📡 Route requested")
    emit("route", {
        "baseline_eta": 48,
        "optimized_eta": 34,
        "thickness": {
            "baseline": 1,
            "optimized": 3
        },
        "timestamp": time.time()
    })

@socketio.on("chat_message")
def handle_chat_message(data):
    print(f"💬 Chat message received: {data['message']}")
    # Broadcast the message to all connected clients
    emit("chat_message", {
        "message": data["message"],
        "sender": data.get("sender", "Anonymous"),
        "timestamp": time.time()
    }, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
