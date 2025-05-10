from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import AsyncServer, ASGIApp
import json
from datetime import datetime
from utils.gtfs_processor import GTFSProcessor
from utils.telemetry_ingest import TelemetryIngestor

class WebSocketHandler:
    def __init__(self, app: FastAPI):
        self.sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*')
        self.app = ASGIApp(self.sio, app)
        self.gtfs = GTFSProcessor()
        self.telemetry = TelemetryIngestor()
        
        # Register event handlers
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('get_route', self.handle_get_route)
        self.sio.on('chat_message', self.handle_chat_message)

    async def handle_connect(self, sid, environ):
        """Handle client connection."""
        print(f"Client connected: {sid}")
        # Send initial route data
        await self.handle_get_route(sid)

    async def handle_disconnect(self, sid):
        """Handle client disconnection."""
        print(f"Client disconnected: {sid}")

    async def handle_get_route(self, sid):
        """Handle route data request."""
        try:
            # Get available trips
            trips = self.gtfs.get_all_trip_ids()
            if not trips:
                return
            
            # Get first trip's coordinates and metadata
            trip_id = trips[0]
            coords = self.gtfs.get_route_coordinates(trip_id)
            metadata = self.gtfs.get_route_metadata(trip_id)
            
            # Get speed data for each coordinate
            speeds = []
            if self.telemetry.is_redis_available():
                for lat, lon in coords:
                    seg_id = f"{lat:.4f},{lon:.4f}"
                    speed = self.telemetry.get_segment_speed(seg_id) or 35.0  # Default speed if not available
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
            
            await self.sio.emit('route', route_data, room=sid)
            
        except Exception as e:
            print(f"Error getting route data: {str(e)}")
            await self.sio.emit('error', {'message': str(e)}, room=sid)

    async def handle_chat_message(self, sid, data):
        """Handle chat messages."""
        try:
            message = {
                'sender': data.get('sender', 'Anonymous'),
                'message': data['message'],
                'timestamp': datetime.now().timestamp()
            }
            await self.sio.emit('chat_message', message)  # Broadcast to all clients
            
        except Exception as e:
            print(f"Error handling chat message: {str(e)}")
            await self.sio.emit('error', {'message': str(e)}, room=sid)
