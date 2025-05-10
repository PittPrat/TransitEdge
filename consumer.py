import argparse
import asyncio
import json
import orjson
import redis
import csv
from pathlib import Path
from azure.eventhub.aio import EventHubConsumerClient

# Configuration values for Event Hub and Redis
EVENT_HUB_CONNECTION_STR = "your_connection_string"  # Connection string for Azure Event Hub
EVENT_HUB_NAME = "your_event_hub"  # Name of the Event Hub to consume data from
REDIS_HOST = "localhost"  # Redis server hostname
REDIS_PORT = 6379  # Redis server port
REDIS_DB = 0  # Redis database index

# Define the output CSV file location inside a 'data' directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CSV_FILE = DATA_DIR / "wsdot_loops.csv"

# Ensure 'data' directory exists
DATA_DIR.mkdir(exist_ok=True)

# Create an Event Hub consumer client for consuming telemetry data
client = EventHubConsumerClient.from_connection_string(EVENT_HUB_CONNECTION_STR, consumer_group="$Default", eventhub_name=EVENT_HUB_NAME)

# Create a Redis client for storing telemetry data
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# Define CSV headers based on expected output format
CSV_HEADERS = ["AverageTime", "CurrentTime", "Description", "Distance", "EndPoint", "Name", "StartPoint", "TimeUpdated", "TravelTimeID"]

async def consume(event):
    """ Processes a single event and stores relevant telemetry data in Redis and CSV. """
    data = orjson.loads(event.body_as_str())  # Deserialize the event data using orjson
    station_id = data["TravelTimeID"]  # Extract unique identifier
    speed = data.get("AverageTime", "N/A")  # Extract relevant metric
    
    # Store speed data in Redis with a key based on station ID
    redis_client.set(f"spd:{station_id}", speed)

    # Write data to CSV
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        if file.tell() == 0:  # Write header only if file is empty
            writer.writeheader()
        writer.writerow(data)

async def event_handler(partition_context, events):
    """ Handles a batch of events from Event Hub. """
    for event in events:
        await consume(event)  # Process each event
    await partition_context.update_checkpoint()  # Commit checkpoint to track processed events

async def run_consumer(dry_run=False):
    """ Starts the Event Hub consumer to continuously receive events. """
    async with client:
        await client.receive(on_event_batch=event_handler, starting_position="-1")  # Consume from earliest available event

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print to console instead of Redis")
    args = parser.parse_args()

    if args.dry_run:
        print("Dry run mode: consuming but not storing in Redis or CSV.")
    
    asyncio.run(run_consumer(dry_run=args.dry_run))
