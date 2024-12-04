import requests


API_KEY = "29fd7aa975e54518a4c9f6a0c5447408"
ROUTING_URL = "https://api.geoapify.com/v1/routing"

start_location = (40.748817, -73.985428)  # Empire State Building
end_location = (40.730610, -73.935242)    # East Village
mode="drive"



def get_instructions(start_location, end_location):
    """
    Fetches the step-by-step directions between two locations using a routing API.

    Parameters:
        start_location (tuple): Coordinates of the start location (latitude, longitude).
        end_location (tuple): Coordinates of the end location (latitude, longitude).

    Returns:
        list: A list of instructions for the route.
    """
    params = {
        "waypoints": f"{start_location[0]},{start_location[1]}|{end_location[0]},{end_location[1]}",
        "mode": mode,  # Modes: drive, walk, bike, etc.
        "apiKey": API_KEY
    }

    # Make the API request
    response = requests.get(ROUTING_URL, params=params)

    # Check the response
    if response.status_code == 200:
        try:
            data = response.json()
            instructions = []
            
            # Safely extract the steps
            if 'features' in data and data['features']:
                legs = data['features'][0]['properties']['legs']
                for leg in legs:
                    steps = leg.get('steps', [])
                    for step in steps:
                        instructions.append(step['instruction']['text'])
            else:
                instructions.append("No routing data found in the response.")
            
            return instructions

        except Exception as e:
            return [f"Error parsing response: {e}"]
    else:
        return [f"API Error: {response.status_code}", response.text]



#
def get_distance_and_time(start_location,end_location):
    """
        Fetches the distance and time between two locations using a routing API.

        Parameters:
            start_location (tuple) (lat,long): Coordinates of the start location (latitude, longitude).
            end_location (tuple)(lat,long): Coordinates of the end location (latitude, longitude).

        Returns:
            list:[distance,time] A list containing the total distance (in meters) and time (in seconds).
    """

    params = {
    "waypoints": f"{start_location[0]},{start_location[1]}|{end_location[0]},{end_location[1]}",
    "mode": mode,  # Modes: drive, walk, bike, etc.
    "apiKey": API_KEY
}

    # Make the API request
    response = requests.get(ROUTING_URL, params=params)

    # Check the response
    if response.status_code == 200:
        try:
            data = response.json()
            # Accessing the distance and time from the starting point
            distance = data['features'][0]['properties']['distance']
            time = data['features'][0]['properties']['time']
            # print(f"Total Distance: {distance} meters")
            # print(f"Total Time: {time} seconds")
            return[distance,time]
        except Exception as e:
            print(f"Error parsing response: {e}")
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)
        
# **************************************
# any time you import geoapify it prints this, so comment it out vvv

# print(get_distance_and_time(start_location,end_location))

# print(get_instructions(start_location,end_location))