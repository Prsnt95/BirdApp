import requests
import jsons
import geoapify


import uuid
import pathlib
import logging
import sys
import os
import base64
import time

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
  Prints out all the trips in the database

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
    api = '/trips'
    url = baseurl + api

    # res = requests.get(url)
    res = requests.get(url)

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
    # deserialize and extract ustripsers:
    #
    body = res.json()

    #
    # let's map each row into a Trip object:
    #
    trips = []
    for row in body:
      trip = Trip(row)
      trips.append(trip)
    #
    # Now we can think OOP:
    #
    if len(trips) == 0:
      print("no trips...")
      return

    for trip in trips:
      print(trip.tripid)
      print(" ", trip.bird_name)
      print(" ", trip.start_loc)
      print(" ", trip.end_loc)
      print(" ", trip.trans_mode)
      print(" ", trip.distance)
      print(" ", trip.instructions)
    #
    return

  except Exception as e:
    logging.error("**ERROR: trips() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  

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
    print("Enter starting address>")
    strt_addr = input()

    print("Enter destination address>")
    dst_addr = input()

    print("Enter transportation mode: (car, bicycle, bus, transit, walk)")
    transport = input()

    data = {"startaddress": strt_addr, "destaddress": dst_addr, "mode": transport}

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
    elif res.status_code == 400: # no such user
      body = res.json()
      print(body)
      return
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
    # success, extract jobid:
    #
    body = res.json()

    jobid = body

    print("Trip created:", jobid)
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
        print("Enter region>")
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
            print(body)  # Print the response data
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
    Outputs recent bird observations nearby

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
        api = '/nearbird'
        print("Enter starting address>")
        addr = input()

        # Construct the full URL with query parameters
        url = f"{baseurl}{api}?address={addr}"
        res = requests.get(url)

        #
        # let's look at what we got back:
        #
        if res.status_code == 200:  # Success
            body = res.json()
            print(body)  # Print the response data
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
        logging.error("**ERROR: nearby_birds() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return

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
