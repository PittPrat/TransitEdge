import asyncio
import signal
import json
import orjson
import csv
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

EVENT_HUB_CONNECTION_STR = "your_connection_string"
EVENT_HUB_NAME = "your_event_hub"
CSV_FILE = "wsdot_loops.csv"
BATCH_SIZE = 100
INTERVAL_SECONDS = 10

producer = EventHubProducerClient.from_connection_string(EVENT_HUB_CONNECTION_STR, eventhub_name=EVENT_HUB_NAME)

async def send_telemetry():
    async with producer:
        while True:
            batch = []
            with open(CSV_FILE, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    batch.append(orjson.dumps(row))
                    if len(batch) == BATCH_SIZE:
                        await producer.send_batch([EventData(body=data) for data in batch])
                        batch = []
                if batch:
                    await producer.send_batch([EventData(body=data) for data in batch])
            await asyncio.sleep(INTERVAL_SECONDS)

def graceful_shutdown(loop):
    loop.stop()

loop = asyncio.get_event_loop()
for sig in (signal.SIGINT, signal.SIGTERM):
    loop.add_signal_handler(sig, lambda: graceful_shutdown(loop))

loop.run_until_complete(send_telemetry())
