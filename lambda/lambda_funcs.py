### ALL THE LAMBDA FUNCTIONS

# Trip planner

import json
import boto3
import os
import datatier
import requests
from configparser import ConfigParser

def lambda_handler(event, context):
    try:
        print("**STARTING**")
        print("**lambda: proj_plan_trip**")

        # Setup AWS based on config file
        config_file = 'benfordapp-config.ini'
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file

        configur = ConfigParser()
        configur.read(config_file)

        # Configure for RDS access
        rds_endpoint = configur.get('rds', 'endpoint')
        rds_portnum = int(configur.get('rds', 'port_number'))
        rds_username = configur.get('rds', 'user_name')
        rds_pwd = configur.get('rds', 'user_pwd')
        rds_dbname = configur.get('rds', 'db_name')

        # Accessing request body
        print("**Accessing request body**")
        if "body" not in event:
            raise Exception("event has no body")

        body = json.loads(event["body"])  # parse the JSON
        if not all(key in body for key in ["birdname", "startaddress","destlat","destlon", "destaddress", "mode"]):
            raise Exception("Missing required parameters in the request body")

        bird_name = body["birdname"]
        start_address = body["startaddress"]
        dest_address = body["destaddress"]
        trans_mode = body["mode"]
        dest_lat = body["destlat"]
        dest_lon = body["destlon"]

        # Geoapify API details
        GEOAPIFY_API_KEY = "29fd7aa975e54518a4c9f6a0c5447408"
        GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
        ROUTING_URL = "https://api.geoapify.com/v1/routing"

        # Geocode start and destination addresses
        def get_coordinates(address):
            params = {"text": address, "apiKey": GEOAPIFY_API_KEY}
            response = requests.get(GEOCODING_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["features"]:
                    coords = data["features"][0]["geometry"]["coordinates"]
                    return coords[1], coords[0]  # Return as (lat, lon)
                else:
                    raise Exception(f"Could not geocode address: {address}")
            else:
                raise Exception(f"Geoapify Geocoding API Error: {response.status_code}")

        start_coords = get_coordinates(start_address)
        #dest_coords = get_coordinates(dest_address)
        dest_coords = (dest_lat, dest_lon)
        # Make routing API request
        params = {
            "waypoints": f"{start_coords[0]},{start_coords[1]}|{dest_coords[0]},{dest_coords[1]}",
            "mode": trans_mode,
            "apiKey": GEOAPIFY_API_KEY
        }
        response = requests.get(ROUTING_URL, params=params)

        if response.status_code == 200:
            routing_data = response.json()
            if "features" in routing_data and routing_data["features"]:
                steps = routing_data["features"][0]["properties"]["legs"][0]["steps"]
                instructions = "\n".join(step["instruction"]["text"] for step in steps)
                distance = routing_data["features"][0]["properties"]["distance"] / 1000  # Convert to kilometers
            else:
                raise Exception("No routing data found")
        else:
            raise Exception(f"Geoapify Routing API Error: {response.status_code}")

        # Open connection to the database
        print("**Opening connection**")
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

        # Add trip to database
        print("**Adding trip to database**")
        sql = """
            INSERT INTO trips (bird_name, start_loc, end_loc, trans_mode, distance, instructions)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        datatier.perform_action(dbConn, sql, [bird_name, start_address, dest_address, trans_mode, distance, instructions])

        # Get the generated trip ID
        sql = "SELECT LAST_INSERT_ID();"
        row = datatier.retrieve_one_row(dbConn, sql)
        trip_id = row[0]

        print("Trip ID:", trip_id)
        print("bird name:", bird_name)
        print("Start address:", start_address)
        print("End address:", dest_address)
        print("Instructions:", instructions)



        # Return the trip ID
        return {
            'statusCode': 200,
            'body': json.dumps({"trip_id": trip_id, "instructions": instructions})
        }

    except Exception as err:
        print("**ERROR**")
        print(str(err))
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(err)})
        }





# download trip func
# Same as trips func, it requires datatier, benford config etc. (see trips func below)


import json
import datatier
from configparser import ConfigParser

def lambda_handler(event, context):
    try:
        print("**STARTING**")
        print("**lambda: proj_download_trip**")

        # Read database configuration
        config_file = 'benfordapp-config.ini'
        configur = ConfigParser()
        configur.read(config_file)

        rds_endpoint = configur.get('rds', 'endpoint')
        rds_portnum = int(configur.get('rds', 'port_number'))
        rds_username = configur.get('rds', 'user_name')
        rds_pwd = configur.get('rds', 'user_pwd')
        rds_dbname = configur.get('rds', 'db_name')

        # Extract trip ID from the event
        if "pathParameters" in event and "id" in event["pathParameters"]:
            trip_id = event["pathParameters"]["id"]
        else:
            raise ValueError("The 'id' parameter is required in pathParameters")

        print(f"Fetching trip with ID: {trip_id}")

        # Open connection to the database
        print("**Opening connection to database**")
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

        # Query the trips table
        print(f"**Querying trips table for ID {trip_id}**")
        sql = "SELECT * FROM trips WHERE id = %s;"
        row = datatier.retrieve_one_row(dbConn, sql, [trip_id])

        if not row:
            print(f"**No trip found with ID {trip_id}**")
            return {
                'statusCode': 404,
                'body': json.dumps({"error": "No trip found with the given ID"})
            }

        # Map the row to JSON-friendly format
        trip_data = {
            "id": row[0],
            "bird_name": row[1],
            "start_loc": row[2],
            "end_loc": row[3],
            "trans_mode": row[4],
            "distance": row[5],
            "instructions": row[6]
        }

        print(f"**Trip data: {trip_data}**")
        
        # Return the trip details
        return {
            'statusCode': 200,
            'body': json.dumps(trip_data)
        }

    except ValueError as ve:
        print("**VALUE ERROR**", str(ve))
        return {
            'statusCode': 400,
            'body': json.dumps({"error": str(ve)})
        }
    except Exception as err:
        print("**ERROR**", str(err))
        return {
            'statusCode': 500,
            'body': json.dumps({"error": "An internal server error occurred"})
        }



# trips func (you need benforappconfig.ini + datatier func, see proj03 users Lambda)

#
# Retrieves and returns all the trips in the 
# BenfordApp database.
#

import json
import boto3
import os
import datatier

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: proj_trips**")
    
    #
    # setup AWS based on config file:
    #
    config_file = 'benfordapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    #
    # open connection to the database:
    #
    print("**Opening connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    
    #
    # now retrieve all the users:
    #
    print("**Retrieving data**")

    #
    # TODO #1 of 1: write sql query to select all users from the 
    # users table, ordered by userid
    #
    sql = "SELECT * FROM trips;"
    
    rows = datatier.retrieve_all_rows(dbConn, sql)
    
    for row in rows:
      print(row)

    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning rows**")
    
    return {
      'statusCode': 200,
      'body': json.dumps(rows)
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }




##### nearby birds

import requests
import json

def lambda_handler(event, context):
    try:
        # Extract the address parameter from the query string
        address = event.get("queryStringParameters", {}).get("address", None)
        address = "Evanston, IL"

        if not address:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Address is required"})
            }

        print(f"Received address: {address}")

        # Step 1: Convert address to latitude and longitude using the OSM Nominatim API
        OSM_API_URL = "https://nominatim.openstreetmap.org/search"
        osm_params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "MyApplication/1.0 (poecileballista@gmail.com)"  # Replace with a valid email
        }

        osm_response = requests.get(OSM_API_URL, params=osm_params, headers=headers)

        if osm_response.status_code != 200:
            print(f"Error fetching coordinates: {osm_response.status_code}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to fetch coordinates for the given address"})
            }

        osm_data = osm_response.json()

        if not osm_data:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "No coordinates found for the given address"})
            }

        # Extract latitude and longitude from the OSM response
        lat = osm_data[0]["lat"]
        lon = osm_data[0]["lon"]
        print(f"Coordinates for address: lat={lat}, lon={lon}")

        # Step 2: Call the eBird API for nearby observations using the coordinates
        EBIRD_API_URL = "https://api.ebird.org/v2/data/obs/geo/recent"
        API_KEY = "nb5l4s4jlcl4"
        headers = {
            "X-eBirdApiToken": API_KEY
        }

        ebird_params = {
            "lat": lat,
            "lng": lon,
            "maxResults": 10
        }

        ebird_response = requests.get(EBIRD_API_URL, headers=headers, params=ebird_params)

        if ebird_response.status_code != 200:
            print(f"Error fetching eBird data: {ebird_response.status_code}")
            return {
                "statusCode": ebird_response.status_code,
                "body": json.dumps({"error": "Failed to fetch data from eBird API"})
            }

        ebird_data = ebird_response.json()
        print(f"Fetched eBird data: {ebird_data}")

        # Step 3: Return the eBird data as the response
        return {
            "statusCode": 200,
            "body": json.dumps(ebird_data)  # JSON-encode the output
        }

    except Exception as err:
        print("**ERROR**")
        print(str(err))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(err)})
        }




##### region birds

import requests
import json

def lambda_handler(event, context):
    try:
        # Extract the region parameter from the query string
        region = event.get("queryStringParameters", {}).get("region", None)
                

        if not region:
            # region = "US-IL"
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Region is required"})
            }

        print(f"Received region: {region}")

        # eBird API details
        API_KEY = "nb5l4s4jlcl4"
        BASE_URL = "https://api.ebird.org/v2"

        headers = {
            "X-eBirdApiToken": API_KEY
        }

        # Construct the URL dynamically using the provided region
        url = f"{BASE_URL}/data/obs/{region}/recent/"

        params = {
            'MaxResults': 10
        }

        # Call the eBird API
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()  # Parse the response JSON
        else:
            print(f"Error: {response.status_code}")
            return {
                "statusCode": response.status_code,
                "body": json.dumps({"error": "Failed to fetch data from eBird"})
            }

        # Return the eBird data as the response
        return {
            'statusCode': 200,
            'body': json.dumps(data)  # JSON-encode the output
        }
    
    except Exception as err:
        print("**ERROR**")
        print(str(err))
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(err)})
        }





## Send Email
import json
import boto3
import os
from configparser import ConfigParser

def lambda_handler(event, context):
    try:
        
        # config file setup:

        config_file = 'benfordapp-config.ini'
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
        
        configur = ConfigParser()
        configur.read(config_file)
        
    #    Ses acess
        ses_region = configur.get('ses', 'region')
        sender_email = configur.get('ses', 'sender_email')
        
    
        print("**Parsing request data**")
        body = json.loads(event['body'])
        recipient_email = body['recipient_email']
        trip_details = body['trip_details']
        
    
        ses_client = boto3.client('ses', region_name=ses_region)
        
        #
        # Prepare email content
        #
        subject = f"Trip Details: {trip_details['bird_name']}"
        body_text = (
            f"Details for Trip:\n\n"
            f"  - Bird Name: {trip_details['bird_name']}\n"
            f"  - Start Location: {trip_details['start_loc']}\n"
            f"  - End Location: {trip_details['end_loc']}\n"
            f"  - Transportation Mode: {trip_details['trans_mode']}\n"
            f"  - Distance: {trip_details['distance']} km\n"
            f"\nInstructions:\n"
            f"{trip_details['instructions']}\n"
        )
        
    
        # Send email
        
        response = ses_client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [recipient_email]
            },
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        
        print("DONE, email sent successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Email sent successfully',
                'messageId': response['MessageId']
            })
        }
        
    except Exception as err:
        print("**ERROR**")
        print(str(err))
        
        return {
            'statusCode': 500,
            'body': json.dumps(str(err))
        }

