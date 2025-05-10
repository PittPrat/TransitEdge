import os
import requests
import csv
import ast

# WSDOT Traveler Information API endpoint and access parameters
API_BASE_URL = "http://www.wsdot.wa.gov/Traffic/api/TravelTimes/TravelTimesREST.svc/GetTravelTimesAsJson"
API_KEY = "43f8f626-3493-4d39-a645-cf86e2443c34"

# Define the latitude and longitude bounds
LAT_MIN, LAT_MAX = 47.5, 48.0
LON_MIN, LON_MAX = -122.5, -122.5

# Directory structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "data", "wsdot_loops.csv")
FILTERED_CSV_FILE = os.path.join(BASE_DIR, "data", "filtered_wsdot_loops.csv")

def get_travel_times():
    """
    Fetch road speed and route travel time data from WSDOT API.
    """
    params = {
        "AccessCode": API_KEY
    }
    try:
        response = requests.get(API_BASE_URL, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        travel_times = response.json()
        return travel_times
    except requests.exceptions.RequestException as e:
        print(f"Error fetching travel times: {e}")
        return None

def save_to_csv(data, filename):
    """
    Save the travel times data to a CSV file.
    """
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(data[0].keys())
        # Write data rows
        for row in data:
            writer.writerow(row.values())

def is_within_bounds(location):
    """ Checks if a given latitude/longitude pair is within the specified bounds. """
    lat = location.get("Latitude", 0)
    lon = location.get("Longitude", 0)
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX

def filter_csv(input_file, output_file):
    """ Reads a CSV file and filters rows based on latitude/longitude bounds. """
    with open(input_file, newline='') as infile, open(output_file, mode='w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            try:
                start_location = ast.literal_eval(row["StartPoint"])
                end_location = ast.literal_eval(row["EndPoint"])

                if is_within_bounds(start_location) and is_within_bounds(end_location):
                    writer.writerow(row)

            except (ValueError, SyntaxError):
                print(f"Skipping row due to invalid location data: {row}")

if __name__ == "__main__":
    travel_data = get_travel_times()
    # Save the data to a CSV file if the API call was successful
    if travel_data:
        save_to_csv(travel_data, CSV_FILE)
        filter_csv(CSV_FILE, FILTERED_CSV_FILE)
    else:
        print("Failed to retrieve data.")