### ALL THE LAMBDA FUNCTIONS



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

