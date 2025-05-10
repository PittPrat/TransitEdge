from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import List, Dict, Any
import os
import requests
import redis
import socketio
from datetime import datetime

# Import utility classes
from utils.gtfs_processor import GTFSProcessor
from utils.telemetry_ingest import TelemetryIngestor

# Load environment variables
load_dotenv()

# Initialize FastAPI app
fastapi_app = FastAPI()

# Enable CORS
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO with engineio_logger for debugging
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Create Socket.IO ASGI app with FastAPI mounted at /api
app = socketio.ASGIApp(
    sio,
    other_asgi_app=fastapi_app,
    socketio_path='socket.io'
)

# Initialize processors
gtfs_processor = GTFSProcessor()
telemetry_ingestor = TelemetryIngestor()

# Get Azure Maps API key
AZURE_KEY = os.getenv("AZURE_MAPS_KEY", "")

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    # Send initial route data
    await handle_get_route(sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def get_route(sid):
    print(f"Route request from {sid}")
    await handle_get_route(sid)

@sio.event
async def chat_message(sid, data):
    try:
        print(f"Chat message from {sid}: {data}")
        if not isinstance(data, dict) or 'message' not in data:
            raise ValueError("Invalid message format")
            
        message = {
            'sender': data.get('sender', 'Anonymous'),
            'message': data['message'],
            'timestamp': datetime.now().timestamp()
        }
        print(f"Broadcasting message: {message}")
        await sio.emit('chat_message', message)  # Broadcast to all clients
    except Exception as e:
        print(f"Error handling chat message: {str(e)}")
        await sio.emit('error', {'message': str(e)}, room=sid)

async def handle_get_route(sid):
    try:
        # Get available trips
        trips = gtfs_processor.get_all_trip_ids()
        if not trips:
            return
        
        # Get first trip's coordinates and metadata
        trip_id = trips[0]
        coords = gtfs_processor.get_route_coordinates(trip_id)
        metadata = gtfs_processor.get_route_metadata(trip_id)
        
        # Get speed data for each coordinate
        speeds = []
        if telemetry_ingestor.is_redis_available():
            for lat, lon in coords:
                seg_id = f"{lat:.4f},{lon:.4f}"
                speed = telemetry_ingestor.get_segment_speed(seg_id) or 35.0  # Default speed if not available
                speeds.append(speed)
        else:
            speeds = [35.0] * len(coords)  # Default speeds if Redis is not available
        
        # Calculate ETAs
        baseline_eta = sum(len(coords) * [35.0])  # Baseline using standard speed
        optimized_eta = sum(speeds)  # Optimized using real-time speeds
        
        route_data = {
            'trip_id': trip_id,
            'coordinates': coords,
            'speeds': speeds,
            'metadata': metadata,
            'baseline_eta': baseline_eta,
            'optimized_eta': optimized_eta,
            'timestamp': datetime.now().timestamp()
        }
        
        await sio.emit('route', route_data, room=sid)
        
    except Exception as e:
        print(f"Error getting route data: {str(e)}")
        await sio.emit('error', {'message': str(e)}, room=sid)


@fastapi_app.get("/")
def read_root():
    return {"message": "TransitEdge backend is running"}

# Fix - change @app.post to @fastapi_app.post
@fastapi_app.post("/route")
async def get_route(request: Request):
    try:
        body = await request.json()
        trip_id = body.get("trip_id")
        if not trip_id:
            raise HTTPException(status_code=400, detail="trip_id is required")

        # Get route coordinates
        coords = load_gtfs(trip_id)
        if not coords:
            raise HTTPException(status_code=404, detail=f"No route found for trip_id: {trip_id}")

        origin = coords[0]
        destination = coords[-1]

        # Get Azure Maps route
        directions = await call_azure_route_directions(origin, destination)
        seconds = directions["routes"][0]["summary"]["travelTimeInSeconds"]
        baseline_minutes = round(seconds / 60)

        # Get live speeds directly from telemetry
        speeds = []
        for i in range(len(coords) - 1):
            seg_id = f"{coords[i][0]:.4f},{coords[i][1]:.4f}"
            speed = telemetry_ingestor.get_segment_speed(seg_id)
            speeds.append(speed)

        # Calculate optimized route
        avg_speed = sum(speeds) / len(speeds) if speeds else 12.0
        optimized_minutes = round(baseline_minutes * (12.0 / avg_speed), 1)
        offset = round(optimized_minutes - baseline_minutes)

        # Get route metadata
        metadata = gtfs_processor.get_route_metadata(trip_id)

        # Log prediction
        prediction_id = f"{trip_id}_{datetime.utcnow().isoformat()}"
        await log_prediction(
            prediction_id=prediction_id,
            actual=baseline_minutes,
            predicted=optimized_minutes,
            metadata={
                "trip_id": trip_id,
                "avg_speed": avg_speed,
                "recommended_departure_offset": offset,
                **metadata
            }
        )

        return {
            "trip_id": trip_id,
            "baseline_minutes": baseline_minutes,
            "optimized_minutes": optimized_minutes,
            "recommended_departure_offset_min": offset,
            "metadata": metadata,
            "co2_savings_kg": calculate_co2_savings(baseline_minutes, optimized_minutes)
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def mock_score(optimized_min, co2=0.1, hov=2, ada=0):
    return optimized_min + co2 * 0.14 - hov * 2


async def call_azure_route_directions(origin: List[float], destination: List[float]) -> Dict[str, Any]:
    """Get route directions from Azure Maps API."""
    url = "https://atlas.microsoft.com/route/directions/json"
    params = {
        "api-version": "1.0",
        "subscription-key": AZURE_KEY,
        "query": f"{origin[0]},{origin[1]}:{destination[0]},{destination[1]}",
        "travelMode": "bus",
        "computeTravelTimeFor": "all",
        "routeType": "eco"
    }

    try:
        response = await requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Azure Maps API error: {str(e)}")

# Fix - change all remaining routes from @app to @fastapi_app
@fastapi_app.get("/live_speed")
async def get_live_speed(seg_id: str) -> Dict[str, Any]:
    """Get live speed for a segment from Redis."""
    try:
        speed = telemetry_ingestor.get_segment_speed(seg_id)
        return {"speed": speed, "segment_id": seg_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.get("/trips")
async def get_available_trips() -> Dict[str, Any]:
    """Get list of all available trips."""
    try:
        trips = gtfs_processor.get_all_trip_ids()
        return {"trips": trips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.get("/route/{trip_id}/metadata")
async def get_route_metadata(trip_id: str) -> Dict[str, Any]:
    """Get metadata for a specific route."""
    try:
        metadata = gtfs_processor.get_route_metadata(trip_id)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def log_prediction(prediction_id, actual, predicted, metadata):
    print(f"[LOG] Prediction ID: {prediction_id}")
    print(f"      Baseline (actual): {actual} min")
    print(f"      Optimized (predicted): {predicted} min")
    print(f"      Metadata: {metadata}")

def calculate_co2_savings(baseline_minutes, optimized_minutes):
    """Calculate CO2 savings based on time difference."""
    # Simple placeholder calculation - replace with actual logic
    return round((baseline_minutes - optimized_minutes) * 0.5, 2)

def load_gtfs(trip_id: str) -> List[List[float]]:
    """Load GTFS coordinates for a trip using GTFSProcessor."""
    coords = gtfs_processor.get_route_coordinates(trip_id)
    return coords if coords else []

# This should be at the end of the file if you're running the server directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5001)