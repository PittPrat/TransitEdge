import asyncio
import signal
import json
import orjson
import csv
from pathlib import Path
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

# Configuration values for Event Hub and data processing
EVENT_HUB_CONNECTION_STR = "your_connection_string"  # Connection string for Azure Event Hub
EVENT_HUB_NAME = "your_event_hub"  # Name of the Event Hub to send data to

# Define the output CSV file location inside a 'data' directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CSV_FILE = DATA_DIR / "wsdot_loops.csv"

# Ensure 'data' directory exists
DATA_DIR.mkdir(exist_ok=True)

BATCH_SIZE = 100  # Maximum number of telemetry records to send in each batch
INTERVAL_SECONDS = 10  # Time interval (in seconds) between data transmission loops

# Create an asynchronous Event Hub producer client using the provided connection string
producer = EventHubProducerClient.from_connection_string(EVENT_HUB_CONNECTION_STR, eventhub_name=EVENT_HUB_NAME)

async def send_telemetry():
    """ Reads telemetry data from a CSV file and sends it to Azure Event Hub in batches. """
    async with producer:
        while True:
            batch = []  # Initialize an empty list to hold telemetry messages
            with open(CSV_FILE, newline='') as csvfile:
                reader = csv.DictReader(csvfile)  # Read the CSV file as a dictionary
                for row in reader:
                    # Ensure only the expected fields are transmitted
                    formatted_data = {
                        "AverageTime": row.get("AverageTime", "N/A"),
                        "CurrentTime": row.get("CurrentTime", "N/A"),
                        "Description": row.get("Description", ""),
                        "Distance": row.get("Distance", 0),
                        "EndPoint": row.get("EndPoint", ""),
                        "Name": row.get("Name", ""),
                        "StartPoint": row.get("StartPoint", ""),
                        "TimeUpdated": row.get("TimeUpdated", ""),
                        "TravelTimeID": row.get("TravelTimeID", "")
                    }
                    batch.append(orjson.dumps(formatted_data))  # Serialize the formatted data

                    if len(batch) == BATCH_SIZE:  # Send data in batches
                        await producer.send_batch([EventData(body=data) for data in batch])
                        batch = []  # Reset the batch after sending
            
                if batch:  # Send any remaining telemetry data
                    await producer.send_batch([EventData(body=data) for data in batch])
            
            await asyncio.sleep(INTERVAL_SECONDS)  # Wait before processing the next batch

def graceful_shutdown(loop):
    """ Handles shutdown signals to properly stop the asyncio event loop. """
    loop.stop()  # Stop the event loop when termination signals are received

# Create an asyncio event loop to manage asynchronous execution
loop = asyncio.get_event_loop()

# Register signal handlers for graceful shutdown (SIGINT for Ctrl+C, SIGTERM for process termination)
for sig in (signal.SIGINT, signal.SIGTERM):
    loop.add_signal_handler(sig, lambda: graceful_shutdown(loop))

# Start the telemetry transmission process asynchronously
loop.run_until_complete(send_telemetry())