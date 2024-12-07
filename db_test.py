import requests
import jsons
import geoapify

from dotenv import load_dotenv


import uuid
import pathlib
import logging
import sys
import os
import base64
import time
import boto3



from configparser import ConfigParser



class Trip:

  def __init__(self, row):
    self.tripid = row[0]
    self.bird_name = row[1]
    self.start_loc = row[2]
    self.end_loc = row[3]
    self.trans_mode = row[4]
    self.distance = row[5]
    self.instructions = row[6]

def prompt():
  """
  Prompts the user and returns the command number

  Parameters
  ----------
  None

  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """
  try:
    print()
    print(">> Enter a command:")
    print("   0 => end")
    print("   1 => past trips")
    print("   2 => plan trip")
    print("   3 => download trip")
    print("   4 => See nearby birds (50 km radius)")
    print("   5 => See birds in region")

    cmd = input()

    if cmd == "":
      cmd = -1
    elif not cmd.isnumeric():
      cmd = -1
    else:
      cmd = int(cmd)

    return cmd

  except Exception as e:
    print("**ERROR")
    print("**ERROR: invalid input")
    print("**ERROR")
    return -1
  

def trips(baseurl):
    """
    Displays a summary of trips and allows the user to view details or return.
    Users can also send an email with trip details.

    Parameters
    ----------
    baseurl: str
        Base URL for the web service.

    Returns
    -------
    None
    """
    try:
        # API endpoint
        api = '/trips'
        url = baseurl + api

        # Make a request to the web service
        res = requests.get(url)

        # Check the response status
        if res.status_code == 200:  # Success
            body = res.json()
        else:  # Failure
            print("Failed with status code:", res.status_code)
            print("URL:", url)
            if res.status_code == 500:
                body = res.json()
                print("Error message:", body.get('message', 'Unknown error'))
            return

        # Map each row into a Trip object
        trips = [Trip(row) for row in body]

        if not trips:
            print("No trips available...")
            return

        # Display bird names and locations
        while True:
            print("\nAvailable Trips:\n")
            for i, trip in enumerate(trips, start=1):
                print(f"{i}. Bird: {trip.bird_name} | Start: {trip.start_loc} | End: {trip.end_loc}")

            print("\nEnter the number of the trip for more info, or '99' to return to the main menu.")
            user_input = input("> ")

            if user_input == '99':  # Exit to main menu
                return

            try:
                trip_index = int(user_input) - 1
                if 0 <= trip_index < len(trips):  # Valid trip selection
                    trip = trips[trip_index]
                    print(f"\nDetails for Trip {trip_index + 1}:")
                    print(f"  - Bird Name: {trip.bird_name}")
                    print(f"  - Start Location: {trip.start_loc}")
                    print(f"  - End Location: {trip.end_loc}")
                    print(f"  - Transportation Mode: {trip.trans_mode}")
                    print(f"  - Distance: {trip.distance} km")
                    print("  - Instructions:")
                    instructions = trip.instructions.split('.')
                    for step in instructions:
                        if step.strip():
                            print(f"      • {step.strip()}.")
                    print("-" * 40)

                    # Prompt to send email
                    print("Would you like to send these details via email? (yes/no)")
                    send_email_choice = input("> ").strip().lower()
                    if send_email_choice == 'yes':
                        print("Enter the recipient's email address:")
                        recipient_email = input("> ").strip()
                        try:
                            send_email(trip, recipient_email)
                            print("Email sent successfully!")
                        except Exception as e:
                            print(f"Failed to send email: {e}")
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number corresponding to a trip or '99' to return.")
    except Exception as e:
        logging.error("**ERROR: trips() failed:")
        logging.error("URL: " + url)
        logging.error(e)
        return
  
def send_email(trip, recipient_email):
   config_file = 'email-client-config.ini'
   configur = ConfigParser()
   configur.read(config_file)
   email_url = configur.get('client', 'webservice')
  
   try:
       trip_details = {
           "bird_name": trip.bird_name,
           "start_loc": trip.start_loc,
           "end_loc": trip.end_loc,
           "trans_mode": trip.trans_mode,
           "distance": trip.distance,
           "instructions": trip.instructions
       }
      
       data = {
           "recipient_email": recipient_email,
           "trip_details": trip_details
       }
      
       api = '/send_email'
       url = email_url + api
      
       response = requests.post(url, json=data)
      
       if response.status_code == 200:
           print("Email sent successfully!")
       else:
           print(f"Failed to send email. Status code: {response.status_code}")
           print(f"Response: {response.text}")
              
   except Exception as e:
       print(f"Error sending email: {str(e)}")


def plan_trip(baseurl):
  """
  Prompts the user for a starting address, destination address, transportation mode

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    print("Enter bird name>")
    bird_name = input()

    print("Enter starting address in detail>")
    strt_addr = input()

    print("Enter destination location name (from output results of 4 or 5>")
    dst_addr = input()
    
    print("Enter destination latitude>")
    dst_lat = input()
    
    print("Enter destination longitude>")
    dst_lon = input()

    print("Enter transportation mode: (drive, bicycle, bus, transit, walk)")
    transport = input()

    #data = {"birdname": bird_name, "startaddress": strt_addr, "destaddress": dst_addr, "mode": transport}
    data = {"birdname": bird_name, "startaddress": strt_addr, "destlat": dst_lat,"destlon": dst_lon,"destaddress": dst_addr, "mode": transport}

    #
    # call the web service:
    #
    api = '/plantrip'
    url = baseurl + api

    # res = requests.get(url)
    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # success, extract trip:
    #
    body = res.json()
    trip_id = body.get('trip_id')
    instructions = body.get('instructions', '').split('\n')

    print("\nTrip Created Successfully!")
    print(f"Trip ID: {trip_id}")
    print("\nInstructions:")
    for step_num, step in enumerate(instructions, start=1):
        print(f"  {step_num}. {step}")

    return

  except Exception as e:
    logging.error("**ERROR: upload() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


def region_birds(baseurl):
    """
    Outputs recent bird observations in the region

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        #
        # call the web service:
        #
        api = '/regionbird'
        print("Enter region (e.g. US-IL)>")
        reg = input()

        # Construct the full URL with query parameters
        url = f"{baseurl}{api}?region={reg}"

        # Send a GET request
        res = requests.get(url)

        #
        # let's look at what we got back:
        #
        if res.status_code == 200:  # Success
            body = res.json()
            if body:
                print(f"\nRecent Bird Observations in Region: {reg}\n" + "-" * 50)
                for bird in body:
                    print(f"  - Common Name: {bird.get('comName', 'Unknown')}")
                    print(f"    Scientific Name: {bird.get('sciName', 'Unknown')}")
                    print(f"    Location: {bird.get('locName', 'Unknown')}")
                    print(f"    Coordinates: ({bird.get('lat', 'Unknown')}, {bird.get('lng', 'Unknown')})")
                    print(f"    **Date Observed: {bird.get('obsDt', 'Unknown')}")
                    print(f"    Number Observed: {bird.get('howMany', 'Unknown')}\n")
                    print("-" * 50)
            else:
                print("No recent bird observations found in the specified region.")
        else:
            # Failed:
            print("Failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code == 500:
                # we'll have an error message
                body = res.json()
                print("Error message:", body)
        return

    except Exception as e:
        logging.error("**ERROR: region_birds() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return

  
def nearby_birds(baseurl):
    """
    Outputs recent bird observations nearby.

    Parameters
    ----------
    baseurl: str
        Base URL for the web service.

    Returns
    -------
    None
    """
    try:
        api = '/nearbird'
        print("Enter starting address>")
        addr = input()

        # Construct the full URL with query parameters
        url = f"{baseurl}{api}?address={addr}"
        res = requests.get(url)


        if res.status_code == 200:  # Success
            body = res.json()
            if body:  # Check if the response contains data
                print("\nRecent Bird Observations Nearby:\n")
                for i, bird in enumerate(body, start=1):
                    print(f"Observation {i}:")
                    print(f"  - Common Name: {bird.get('comName', 'Unknown')}")
                    print(f"  - Scientific Name: {bird.get('sciName', 'Unknown')}")
                    print(f"  - Location: {bird.get('locName', 'Unknown')}")
                    print(f"  - Latitude: {bird.get('lat', 'Unknown')}")
                    print(f"  - Longitude: {bird.get('lng', 'Unknown')}")
                    print(f"  - Date Observed: {bird.get('obsDt', 'Unknown')}")
                    print(f"  - Number Observed: {bird.get('howMany', 'Unknown')}")
                    print(f"  - Location Private: {bird.get('locationPrivate', 'Unknown')}")
                    print("-" * 40)
            else:
                print("No bird observations found nearby.")
        else:
            # Handle failure
            print("Failed with status code:", res.status_code)
            print("URL:", url)
            if res.status_code == 500:
                body = res.json()
                print("Error message:", body.get('message', 'Unknown error'))
    except Exception as e:
        logging.error("**ERROR: nearby_birds() failed:")
        logging.error("URL: " + url)
        logging.error(e)


#############################
# Here's what download_trip will receive from the Lambda:
#
#         trip_data = {
        #     "id": row[0],
        #     "bird_name": row[1],
        #     "start_loc": row[2],
        #     "end_loc": row[3],
        #     "trans_mode": row[4],
        #     "distance": row[5],
        #     "instructions": row[6]
        # }
#
#
## Helper function 1 - create textfile 

def create_text_file(trip_data):
    content = ""
    for key, value in trip_data.items():
        content += f"{'-' * 30}\n{key}\n{'-' * 30}\n    {value}\n\n" 
    current_directory = os.getcwd()
    file_path = os.path.join(current_directory, "trip_data.txt")
    with open(file_path, "w") as file:
        file.write(content)
    return file_path

def download_trip(baseurl):
    """
    Prompts the user for the trip id, and downloads
    that trip (into .txt).

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """
  
    try:
        print("Enter trip id>")
        tripid = input()
    
        #
        # call the web service:
        #

        api = '/trips/'
        url = baseurl + api + tripid
        res = requests.get(url)


        # TODO
        # once you receive the res.json grab the fields and then create a txt


        #
        # let's look at what we got back:
        #
        if res.status_code == 200: #success
            # TODO ()
            body = res.json()
            print(body)  # printing response body for now...
            # etc......
        else:
            # Failed:
            print("Failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code == 500:
                # we'll have an error message
                body = res.json()
                print("Error message:", body)
            return
        
       
        
        #if output was list
        #row = res.json()
        '''
        trip_data = {
            "id": row[0],
            "bird_name": row[1],
            "start_loc": row[2],
            "end_loc": row[3],
            "trans_mode": row[4],
            "distance": row[5],
            "instructions": row[6]
        }
        '''
        trip_data = res.json()
        file_path = create_text_file(trip_data)

        print(file_path)
        return

    except Exception as e:
        logging.error("**ERROR: nearby_birds() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return




# ****************************************************
# MAIN
# ****************************************************
try:
  print('** Welcome to BirdApp **')
  print()
#   print('Please enter your state>')
#   state = input()
#   print('Thank you, now please enter your starting address>')
#   strt_addr = input()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  #
  # what config file should we use for this session?
  #
  config_file = 'benfordapp-client-config.ini'

  print("Config file to use for this session?")
  print("Press ENTER to use default, or")
  print("enter config file name>")
  s = input()

  if s == "":  # use default
    pass  # already set
  else:
    config_file = s

  #
  # does config file exist?
  #
  if not pathlib.Path(config_file).is_file():
    print("**ERROR: config file '", config_file, "' does not exist, exiting")
    sys.exit(0)

  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(config_file)
  baseurl = configur.get('client', 'webservice')

  #
  # make sure baseurl does not end with /, if so remove:
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]




  #
  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    #
    if cmd == 1:
      trips(baseurl)
    elif cmd == 2:
       plan_trip(baseurl)
    elif cmd == 3:
       download_trip(baseurl)
    elif cmd == 4:
      nearby_birds(baseurl)
    elif cmd == 5:
      region_birds(baseurl)
    # elif cmd == 2:
    #   jobs(baseurl)
    # elif cmd == 3:
    #   reset(baseurl)
    # elif cmd == 4:
    #   upload(baseurl)
    # elif cmd == 5:
    #   download(baseurl)
    # elif cmd==9:
    #   test()
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
