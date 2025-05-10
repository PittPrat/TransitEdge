import asyncio
import signal
import json
import orjson
import csv
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

# Configuration values for Event Hub and data processing
EVENT_HUB_CONNECTION_STR = "your_connection_string"  # Connection string for Azure Event Hub
EVENT_HUB_NAME = "your_event_hub"  # Name of the Event Hub to send data to
CSV_FILE = "wsdot_loops.csv"  # Path to the CSV file containing telemetry data
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
                    batch.append(orjson.dumps(row))  # Serialize each row using orjson for efficiency
                    if len(batch) == BATCH_SIZE:  # Check if the batch size limit is reached
                        await producer.send_batch([EventData(body=data) for data in batch])  # Send batch to Event Hub
                        batch = []  # Reset the batch after sending
                if batch:  # Send any remaining telemetry data that didn’t fit the batch size exactly
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
