import pytest
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import redis
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.gtfs_processor import GTFSProcessor, DataNotFoundError, InvalidTripError
from utils.telemetry_ingest import TelemetryIngestor, RedisConnectionError

# Test data setup
TEST_DATA = {
    'trip_id': ['SEA_RED_1', 'SEA_RED_1', 'SEA_BEL_1'],
    'latitude': [47.60, 47.61, 47.62],
    'longitude': [-122.33, -122.34, -122.35],
    'route_name': ['Seattle-Redmond', 'Seattle-Redmond', 'Seattle-Bellevue'],
    'route_type': ['BUS', 'BUS', 'BUS'],
    'direction': ['Outbound', 'Outbound', 'Inbound'],
    'speed': [35.0, 40.0, 30.0]
}

@pytest.fixture
def test_data_file(tmp_path):
    """Create a temporary test data file."""
    df = pd.DataFrame(TEST_DATA)
    file_path = tmp_path / "filtered_wsdot_loops.csv"
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def gtfs_processor(tmp_path):
    """Create a GTFSProcessor instance with test data."""
    return GTFSProcessor(str(tmp_path))

@pytest.fixture
def telemetry_ingestor(tmp_path):
    """Create a TelemetryIngestor instance with test data."""
    return TelemetryIngestor()

def test_gtfs_data_loading(gtfs_processor, test_data_file):
    """Test GTFS data loading functionality."""
    gtfs_processor.load_data()
    assert gtfs_processor.routes_df is not None
    assert len(gtfs_processor.routes_df) == 3

def test_route_coordinates(gtfs_processor, test_data_file):
    """Test route coordinate retrieval."""
    coords = gtfs_processor.get_route_coordinates('SEA_RED_1')
    assert len(coords) == 2
    assert coords[0] == (47.60, -122.33)
    assert coords[1] == (47.61, -122.34)

def test_invalid_trip(gtfs_processor, test_data_file):
    """Test handling of invalid trip IDs."""
    with pytest.raises(InvalidTripError):
        gtfs_processor.get_route_coordinates('INVALID_TRIP')

@pytest.mark.skipif(not TelemetryIngestor().is_redis_available(),
              reason="Redis is not available")
def test_telemetry_processing(telemetry_ingestor, test_data_file):
    """Test telemetry data processing."""
    telemetry_ingestor.process_traffic_data(test_data_file)
    speed = telemetry_ingestor.get_segment_speed("47.6000,-122.3300")
    assert abs(speed - 35.0) < 0.1

def test_integration_flow(gtfs_processor, telemetry_ingestor, test_data_file):
    """Test the complete integration flow."""
    # 1. Load GTFS data
    gtfs_processor.load_data()
    
    # 2. Get route coordinates
    coords = gtfs_processor.get_route_coordinates('SEA_RED_1')
    assert len(coords) > 0
    
    # 3. Process telemetry data and get speeds if Redis is available
    if telemetry_ingestor.is_redis_available():
        telemetry_ingestor.process_traffic_data(test_data_file)
        
        # 4. Get speeds for route segments
        speeds = []
        for coord in coords:
            seg_id = f"{coord[0]:.4f},{coord[1]:.4f}"
            speed = telemetry_ingestor.get_segment_speed(seg_id)
            speeds.append(speed)
        
        assert len(speeds) == len(coords)
        assert all(s > 0 for s in speeds)
    else:
        pytest.skip("Redis not available")

def test_metadata_retrieval(gtfs_processor, test_data_file):
    """Test route metadata retrieval."""
    metadata = gtfs_processor.get_route_metadata('SEA_RED_1')
    assert metadata['route_name'] == 'Seattle-Redmond'
    assert metadata['route_type'] == 'BUS'
    assert metadata['direction'] == 'Outbound'
    assert metadata['total_stops'] == 2

if __name__ == '__main__':
    pytest.main([__file__])
