import requests


API_KEY = "nb5l4s4jlcl4"
BASE_URL = "https://api.ebird.org/v2"

def test():
    print("Testing eBird API")

    # Headers for authentication
    headers = {
        "X-eBirdApiToken": API_KEY
    }

    # Function to get recent observations of a species
    def get_recent_observations(region, species_code):
        url = f"{BASE_URL}/data/obs/{region}/recent/{species_code}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()  # Parse JSON response
        else:
            print(f"Error: {response.status_code}")
            return None

    # Function to convert latitude and longitude to a place name using Nominatim
    # Function to convert latitude and longitude to a place name using Nominatim
    def get_place_name(lat, lon):
        geocode_url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,  # Latitude
            "lon": lon,  # Longitude
            "format": "json",  # JSON response
            "addressdetails": 1  # Include detailed address info (optional)
        }
        headers = {
            "User-Agent": "MyApplication/1.0 (your_email@example.com)"  # Replace with a valid email
        }
        
        response = requests.get(geocode_url, params=params, headers=headers)

        if response.status_code == 200:
            try:
                data = response.json()
                return data.get("display_name", "Unknown location")  # Return place name or default
            except ValueError:
                return "Invalid JSON response"
        else:
            return f"Error: {response.status_code}"  # Return error status

    # Example usage
    region_code = "US-IL"  # Illinois, USA
    species_code = "daejun"  # Example species code

    
    data = get_recent_observations(region_code, species_code)

    length = len(data) if len(data) <= 10 else 10
    if data:
        for i in range(length):
            observation=data[i]
            lat = observation.get("lat")
            lng = observation.get("lng")

            if lat and lng:
                place_name = get_place_name(lat, lng)
                print(f"{i}:")
                print(f"Latitude: {lat}, Longitude: {lng}")
                print("Address:", place_name)
            else:
                print("No coordinates available for this observation.")
    else:
        print("No data retrieved.")

test()
