import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import os
from pathlib import Path
from datetime import datetime, timedelta
from functools import lru_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataNotFoundError(Exception):
    """Raised when required data files are not found."""
    pass

class InvalidTripError(Exception):
    """Raised when a trip_id is not found in the data."""
    pass

class GTFSProcessor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.routes_df: Optional[pd.DataFrame] = None
        self.last_load_time: Optional[datetime] = None
        self.reload_interval = timedelta(minutes=5)  # Reload data every 5 minutes

    def should_reload(self) -> bool:
        """Check if data should be reloaded based on time interval."""
        if self.last_load_time is None:
            return True
        return datetime.now() - self.last_load_time > self.reload_interval

    def load_data(self) -> None:
        """Load GTFS data from CSV files with error handling and logging."""
        if not self.should_reload() and self.routes_df is not None:
            return

        try:
            file_path = self.data_dir / "filtered_wsdot_loops.csv"
            if not file_path.exists():
                raise DataNotFoundError(f"GTFS data file not found: {file_path}")

            self.routes_df = pd.read_csv(file_path)
            self.last_load_time = datetime.now()
            logger.info(f"Loaded {len(self.routes_df)} routes from GTFS data")

            # Validate required columns
            required_columns = ['trip_id', 'latitude', 'longitude', 'route_name', 'route_type', 'direction']
            missing_columns = [col for col in required_columns if col not in self.routes_df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in GTFS data: {missing_columns}")

        except (FileNotFoundError, pd.errors.EmptyDataError) as e:
            logger.error(f"Error loading GTFS data: {str(e)}")
            raise DataNotFoundError(f"Failed to load GTFS data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error loading GTFS data: {str(e)}")
            raise

    @lru_cache(maxsize=100)
    def get_route_coordinates(self, trip_id: str) -> List[Tuple[float, float]]:
        """Get list of coordinates for a given trip with caching."""
        try:
            if self.routes_df is None or self.should_reload():
                self.load_data()

            route_data = self.routes_df[self.routes_df['trip_id'] == trip_id]
            if route_data.empty:
                raise InvalidTripError(f"No route found for trip_id: {trip_id}")

            # Sort by sequence number if available
            if 'stop_sequence' in route_data.columns:
                route_data = route_data.sort_values('stop_sequence')

            coords = list(zip(
                route_data['latitude'].tolist(),
                route_data['longitude'].tolist()
            ))

            if not coords:
                raise ValueError(f"No coordinates found for trip_id: {trip_id}")

            return coords

        except InvalidTripError:
            logger.warning(f"Invalid trip_id requested: {trip_id}")
            raise
        except Exception as e:
            logger.error(f"Error getting route coordinates: {str(e)}")
            raise

    @lru_cache(maxsize=1)  # Cache for the reload interval
    def get_all_trip_ids(self) -> List[str]:
        """Get list of all available trip IDs with caching."""
        try:
            if self.routes_df is None or self.should_reload():
                self.load_data()

            trip_ids = self.routes_df['trip_id'].unique().tolist()
            logger.info(f"Found {len(trip_ids)} unique trip IDs")
            return trip_ids

        except Exception as e:
            logger.error(f"Error getting trip IDs: {str(e)}")
            raise

    @lru_cache(maxsize=100)
    def get_route_metadata(self, trip_id: str) -> Dict[str, Any]:
        """Get metadata for a specific route with caching."""
        try:
            if self.routes_df is None or self.should_reload():
                self.load_data()

            route_data = self.routes_df[self.routes_df['trip_id'] == trip_id]
            if route_data.empty:
                raise InvalidTripError(f"No route found for trip_id: {trip_id}")

            first_stop = route_data.iloc[0]
            coords = self.get_route_coordinates(trip_id)

            metadata = {
                'route_name': first_stop.get('route_name', ''),
                'route_type': first_stop.get('route_type', ''),
                'direction': first_stop.get('direction', ''),
                'total_stops': len(coords),
                'start_time': first_stop.get('start_time', ''),
                'end_time': first_stop.get('end_time', ''),
                'distance_km': self._calculate_route_distance(coords)
            }

            logger.debug(f"Retrieved metadata for trip_id: {trip_id}")
            return metadata

        except InvalidTripError:
            logger.warning(f"Invalid trip_id requested: {trip_id}")
            raise
        except Exception as e:
            logger.error(f"Error getting route metadata: {str(e)}")
            raise

    def _calculate_route_distance(self, coords: List[Tuple[float, float]]) -> float:
        """Calculate total route distance in kilometers."""
        from math import radians, sin, cos, sqrt, atan2

        def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            R = 6371  # Earth's radius in kilometers

            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c

        total_distance = 0.0
        for i in range(len(coords)-1):
            total_distance += haversine_distance(
                coords[i][0], coords[i][1],
                coords[i+1][0], coords[i+1][1]
            )

        return round(total_distance, 2)
