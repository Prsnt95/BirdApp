#
# Client-side python app for benford app, which is calling
# a set of lambda functions in AWS through API Gateway.
# The overall purpose of the app is to process a PDF and
# see if the numeric values in the PDF adhere to Benford's
# law.
#
# Authors:
#   << binaryBirds >>
#
#   Prof. Joe Hummel (initial template)
#   Northwestern University
#   CS 310
#

import requests
import jsons

import uuid
import pathlib
import logging
import sys
import os
import base64
import time

from configparser import ConfigParser


############################################################
#
# classes
#?????????????????????????????????????????????????????????????
#?????????????????? UPDATE BASED ON TABLES IN DATABASE########
#?????????????????????????????????????????????????????????????
class User:

  def __init__(self, row):
    self.userid = row[0]
    self.username = row[1]
    self.pwdhash = row[2]


class Job:

  def __init__(self, row):
    self.jobid = row[0]
    self.userid = row[1]
    self.status = row[2]
    self.originaldatafile = row[3]
    self.datafilekey = row[4]
    self.resultsfilekey = row[5]


###################################################################
#
# web_service_get
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_get(url):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url)
        
      if response.status_code in [200, 400, 480, 481, 482, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
    

############################################################
#
# prompt
#
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
    #print("   1 => previous requests")
    print("   2 => plan trip")
    #print("   3 => sort locations by nearest")


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


############################################################
# ADD ALL FUNCTIONS NEEDED 
############################################################
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
############################################################
#PLAN BIRDS
def plan_trip(baseurl):
    """
      Prompts the user for their origin address, bird of interest, 
      radius of search, region of interest
    
      Parameters
      ----------
      baseurl: baseurl for web service
    
      Returns
      -------
      planned  trip from origin to location of birds of interest in the region
      of interest
      """
    try:
      #
      # call the web service:
      #
      print("Enter the start address (street, city, state, zipcode)>")
      origin_address = input()
      
      print("Enter your region of interest>")
      region_interest = input()
      
      print("Enter your bird of interest>")
      bird_interest = input()
      
      print("Enter the maximum radius of search in miles>")
      max_radius = input()
      
      ##????????????check that it is an integer
      
      
      ## ???????????????Process  the origin address before adding it to API
      ### maybe input latitude and longitude????
      
      
      api = '/plan_trip' ##??????????????????
      url = baseurl + api + '/' + origin_address
      
      # res = requests.get(url)
      res = web_service_get(url)
      
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
    
      row = res.json()
      

      trip_data = {
          "id": row[0],
          "bird_name": row[1],
          "start_loc": row[2],
          "end_loc": row[3],
          "trans_mode": row[4],
          "distance": row[5],
          "instructions": row[6]
      }

      file_path = create_text_file(trip_data)

      print(file_path)
      return

    except Exception as e:
      logging.error("**ERROR: download() failed:")
      logging.error("url: " + url)
      logging.error(e)
      return

############################################################
# main
#
try:
  print('** Welcome to BirdApp **')
  print()

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
    if cmd == 2:
        plan_trip(baseurl)
  
    else:
      print("** Unknown command, try again...")
    
    '''
    elif cmd == 2:
      jobs(baseurl)
    elif cmd == 3:
      reset(baseurl)
    elif cmd == 4:
      upload(baseurl)
    elif cmd == 5:
      download(baseurl)
    '''
    
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