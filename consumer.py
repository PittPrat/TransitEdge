import argparse
import asyncio
import json
import orjson
import redis
from azure.eventhub.aio import EventHubConsumerClient

EVENT_HUB_CONNECTION_STR = "your_connection_string"
EVENT_HUB_NAME = "your_event_hub"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

client = EventHubConsumerClient.from_connection_string(EVENT_HUB_CONNECTION_STR, consumer_group="$Default", eventhub_name=EVENT_HUB_NAME)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

async def consume(event):
    data = orjson.loads(event.body_as_str())
    station_id = data["station_id"]
    speed = data["speed_mph"]
    redis_client.set(f"spd:{station_id}", speed)

async def event_handler(partition_context, events):
    for event in events:
        await consume(event)
    await partition_context.update_checkpoint()

async def run_consumer(dry_run=False):
    async with client:
        await client.receive(on_event_batch=event_handler, starting_position="-1")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print to console instead of Redis")
    args = parser.parse_args()

    if args.dry_run:
        print("Dry run mode: consuming but not storing in Redis.")
    
    asyncio.run(run_consumer(dry_run=args.dry_run))
