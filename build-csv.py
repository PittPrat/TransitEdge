import os
import requests

# WSDOT Traveler Information API endpoint and access parameters
API_BASE_URL = "http://www.wsdot.wa.gov/Traffic/api/TravelTimes/TravelTimesREST.svc/GetTravelTimesAsJson"
API_KEY = "43f8f626-3493-4d39-a645-cf86e2443c34"

# Directory structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "data", "wsdot_loops.csv")

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
    import csv
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(data[0].keys())
        # Write data rows
        for row in data:
            writer.writerow(row.values())
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    travel_data = get_travel_times()
    # Save the data to a CSV file if the API call was successful
    if travel_data:
        save_to_csv(travel_data, CSV_FILE)
    else:
        print("Failed to retrieve data.")