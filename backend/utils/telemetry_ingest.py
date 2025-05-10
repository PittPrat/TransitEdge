import redis
import pandas as pd
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import time
from contextlib import contextmanager

load_dotenv()

class RedisConnectionError(Exception):
    """Custom exception for Redis connection issues."""
    pass

class TelemetryIngestor:
    def __init__(self, redis_url: str = "redis://localhost:6379/0", data_dir: str = "data"):
        self.redis_url = redis_url
        self.data_dir = data_dir
        self._redis_client = None

    def is_redis_available(self) -> bool:
        """Check if Redis is available."""
        try:
            client = redis.from_url(self.redis_url)
            client.ping()
            return True
        except (redis.ConnectionError, redis.ResponseError):
            return False

    @property
    def redis_client(self) -> redis.Redis:
        """Lazy Redis connection initialization."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(self.redis_url)
                self._redis_client.ping()  # Test connection
            except redis.ConnectionError as e:
                raise RedisConnectionError(f"Failed to connect to Redis: {str(e)}")
        return self._redis_client

    @contextmanager
    def redis_connection(self):
        """Context manager for Redis operations."""
        try:
            yield self.redis_client
        except redis.ConnectionError as e:
            self._redis_client = None  # Reset connection
            raise RedisConnectionError(f"Redis connection error: {str(e)}")
        except Exception as e:
            raise

    def process_traffic_data(self, csv_file: str) -> None:
        """Process traffic data from CSV and store in Redis."""
        try:
            df = pd.read_csv(os.path.join(self.data_dir, csv_file))
            
            # Group by segment
            segments = df.groupby(['latitude', 'longitude'])
            
            with self.redis_connection() as redis_conn:
                pipeline = redis_conn.pipeline()
                
                for (lat, lon), group in segments:
                    segment_id = f"{lat:.4f},{lon:.4f}"
                    
                    # Calculate average speed for segment
                    avg_speed = group['speed'].mean()
                    
                    # Add to pipeline with 5-minute expiry
                    pipeline.setex(
                        f"speed:{segment_id}",
                        300,  # 5 minutes TTL
                        str(avg_speed)
                    )
                
                # Execute all commands in pipeline
                pipeline.execute()
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Traffic data file not found: {csv_file}")
        except pd.errors.EmptyDataError:
            raise ValueError(f"Traffic data file is empty: {csv_file}")
        except Exception as e:
            raise RuntimeError(f"Error processing traffic data: {str(e)}")

    def stream_live_data(self, csv_file: str, interval: int = 90) -> None:
        """Stream traffic data continuously with specified interval."""
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                self.process_traffic_data(csv_file)
                print(f"[{datetime.now()}] Updated traffic data")
                retry_count = 0  # Reset retry count on success
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\nStopping data stream...")
                break
                
            except RedisConnectionError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"Failed to connect to Redis after {max_retries} attempts. Stopping stream.")
                    break
                print(f"Redis connection error (attempt {retry_count}/{max_retries}): {str(e)}")
                time.sleep(5 * retry_count)  # Exponential backoff
                
            except Exception as e:
                print(f"Error processing data: {str(e)}")
                time.sleep(5)

    def get_segment_speed(self, segment_id: str) -> float:
        """Get current speed for a segment."""
        try:
            with self.redis_connection() as redis_conn:
                speed = redis_conn.get(f"speed:{segment_id}")
                if speed is not None:
                    try:
                        return float(speed)
                    except ValueError:
                        print(f"Warning: Invalid speed value in Redis for segment {segment_id}")
        except RedisConnectionError as e:
            print(f"Warning: Redis connection error: {str(e)}")
        except Exception as e:
            print(f"Warning: Error getting speed for segment {segment_id}: {str(e)}")
        
        return 12.0  # Default speed if any error occurs

if __name__ == "__main__":
    ingestor = TelemetryIngestor()
    ingestor.stream_live_data("filtered_wsdot_loops.csv")
