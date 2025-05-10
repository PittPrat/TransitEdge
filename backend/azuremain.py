from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from phoenix.trace import trace



app = FastAPI()
load_dotenv()

# Azure Maps Key
AZURE_KEY = os.getenv("AZURE_MAPS_SUBSCRIPTION_KEY")

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "TransitEdge backend is running"}

@app.post("/route")
async def get_route(request: Request):
    body = await request.json()
    trip_id = body.get("trip_id", "unknown")

    coords = load_gtfs(trip_id)
    origin = coords[0]
    destination = coords[-1]

    try:
        directions = call_azure_route_directions(origin, destination)
        seconds = directions["routes"][0]["summary"]["travelTimeInSeconds"]
        baseline_minutes = round(seconds / 60)

        prediction_id = f"{trip_id}_{datetime.utcnow().isoformat()}"
        


        # Mock optimization
        speeds = []
        for i in range(len(coords) - 1):
            seg_id = f"{coords[i]}-{coords[i+1]}"
            resp = requests.get(f"http://localhost:8000/live_speed?seg_id={seg_id}")
            speed = float(resp.json().get("speed", 12.0))  # default to 12 mph
            speeds.append(speed)
    
        avg_speed = sum(speeds) / len(speeds)
        optimized_minutes = round(baseline_minutes * (avg_speed / 12.0), 1)
        offset = round(baseline_minutes - optimized_minutes)



        log_prediction(
            prediction_id=prediction_id,
        actual=baseline_minutes,
        predicted=optimized_minutes,
        metadata={
            "trip_id": trip_id,
            "avg_speed": avg_speed,
            "recommended_departure_offset": offset
        }
)

    except Exception as e:
        return {"error": str(e)}

    return {
        "trip_id": trip_id,
        "baseline_minutes": baseline_minutes,
        "optimized_minutes": optimized_minutes,
        "recommended_departure_offset_min": offset
    }


def mock_score(optimized_min, co2=0.1, hov=2, ada=0):
    return optimized_min + co2 * 0.14 - hov * 2


def call_azure_route_directions(origin, destination):
    url = "https://atlas.microsoft.com/route/directions/json"
    params = {
        "api-version": "1.0",
        "subscription-key": AZURE_KEY,
        "query": f"{origin[0]},{origin[1]}:{destination[0]},{destination[1]}",
        "travelMode": "bus"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

@app.get("/live_speed")
def mock_live_speed(seg_id: str):
    return {"speed": 11.5}  # fallback speed (mph) Mocked for now

#Log this later for Phoenix
def log_prediction(prediction_id, baseline, optimized):
    print(f"[LOG] Prediction ID: {prediction_id}")
    print(f"      Baseline (actual): {actual} min")
    print(f"      Optimized (predicted): {predicted} min")
    print(f"      Metadata: {metadata}")



def load_gtfs(trip_id):
    # Simulated GTFS for now
    return [(47.60, -122.33), (47.61, -122.34), (47.62, -122.35)]
