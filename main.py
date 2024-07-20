#
# Client-side python app for IKEA app, which is calling
# a set of lambda functions in AWS through API Gateway.
#
# Authors:
#   Karen Lee, Bhavi Barnwal
#   Northwestern University
#   CS 310
#

import requests
import jsons
import json

import uuid
import pathlib
import logging
import sys
import os
import base64

from configparser import ConfigParser


############################################################
#
# classes
#
class Product:

  def __init__(self, row):
    self.product_id = row[0]
    self.product_title = row[1]
    self.product_price = row[2]


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
  print()
  print(">> Enter a command:")
  print("   0 => end")
  print("   1 => recommend product")
  print("   2 => get product's url")
  print("   3 => upload to cart")
  print("   4 => list out shopping cart")
  print("   5 => remove item from cart")
  print("   6 => download shopping list")
  # print("   7 => clear cart")

  cmd = input()

  if cmd == "":
    cmd = -1
  elif not cmd.isnumeric():
    cmd = -1
  else:
    cmd = int(cmd)

  return cmd


############################################################
#
# recommend
#
def recommend(baseurl):
  """
    Prints out 5 recommended products at a time based on user input

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

  try:
    #
    # get user input:
    #
    search = input("Enter your search: ")
    budget = input("Enter your budget: ")

    #
    # build message:
    #
    data = {"search": str(search), "budget": budget}

    #
    # call the web service:
    #
    api = '/recommend'
    url = baseurl + api

    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      return

    #
    # success, extract product url:
    #
    body = res.json()

    #
    # let's map each row into an Product object:
    #
    recs = []
    for row in body:
      rec = [row["product_id"], row["product_url"]]
      recs.append(rec)

    #
    # Now we can think OOP:
    #
    if len(recs) == 0:
      print("no matching product found...")
      return

    #
    # print out when less than 5 recommended products
    #
    if len(recs) < 5:
      for rec in recs:
        print("Product ID:  ", rec[0])
        print("       URL:  ", rec[1])
      print("\nno more recommended products...")
      return

    #
    # print out the first 5 recommended products
    #
    for i in range(5):
      print("Product ID:  ", recs[i][0])
      print("       URL:  ", recs[i][1])

    #
    # initialize boolean and counters
    #
    bool = "y"
    # represents page counter
    a = 1
    # represents products counter
    counter = 5

    #
    # print out the rest of the recommended products 5 at a time
    #
    while bool == "y":
      while counter < 5 * a:
        # break if no more recommended products left
        if counter > len(recs) - 1:
          print("\nno more recommended products...")
          bool = "n"
          break
        print("Product ID:  ", recs[counter][0])
        print("       URL:  ", recs[counter][1])
        # increment product counter
        counter += 1
      # increment page counter
      a += 1
      if bool == "y":
        bool = input("\nWould you like to see more results? (y/n) ")
        # check that user enters y or n
        if bool != "y" and bool != "n":
          print("must answer with y or n!")
          bool = input("\nWould you like to see more results? (y/n) ")
    return

  except Exception as e:
    logging.error("recommend() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# get_product_url
#
def get_product_url(baseurl):
  """
    Client enters product ID and gets back product URL

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """
  #
  # get user input:
  #
  print("Enter product id>")
  productid = input()

  try:
    #
    # build message:
    #
    data = {"product_id": productid}

    #
    # call the web service:
    #
    api = '/get_product_url'
    url = baseurl + api

    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # get product_url from server side:
    #
    body = res.json()
    product_url = body

    #
    # Now we can think OOP:
    #
    if len(body) == 0:
      print("no product with product ID: ", productid)
      return

    #
    # print out product ID: product URL
    #
    print("Product ID: ", productid)
    print("Product URL: ", product_url)
    return

  except Exception as e:
    logging.error("users() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# upload
#
def upload(baseurl):
  """
  Prompts the user for a local filename and product id, 
  and uploads that asset (jpg) to S3 for processing.

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  #
  # get user input
  #
  print("Enter jpg filename>")
  local_filename = input()

  if not pathlib.Path(local_filename).is_file():
    print("jpg file '", local_filename, "' does not exist...")
    return

  print("Enter product id>")
  productid = input()

  try:
    #
    # build the data packet:
    #
    infile = open(local_filename, "rb")
    bytes = infile.read()
    infile.close()

    #
    # now encode the png as base64. Note b64encode returns
    # a bytes object, not a string. So then we have to convert
    # (decode) the bytes -> string, and then we can serialize
    # the string as JSON for upload to server:
    #
    data = base64.b64encode(bytes)
    datastr = data.decode()

    #
    # build message:
    #
    data = {
        "productid": productid,
        "filename": str(local_filename),
        "data": str(datastr)
    }
    print("data: ", data["productid"])

    #
    # call the web service:
    #
    api = '/upload'
    url = baseurl + api
    res = requests.post(url, json=data)
    print("res: ", res)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      return

    #
    # success, extract producturl:
    #
    body = res.json()
    producturl = body
    return

  except Exception as e:
    logging.error("upload() failed:")
    logging.error("url: " + producturl)
    logging.error(e)
    return


  ############################################################
  #
  # list
  #
def list(baseurl):
  """
    Prints out the information for each product
    in the shopping cart

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
    api = '/list'
    url = baseurl + api

    res = requests.get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      return

    #
    # deserialize and extract users:
    #
    body = res.json()

    #
    # let's map each row into a Product object:
    #
    products = []
    for row in body:
      product = Product(row)
      products.append(product)

    #
    # Now we can think OOP:
    #
    if len(products) == 0:
      print("no products...")
      return

    #
    # initialize total price and total items
    #
    total_price = 0
    items = 0

    #
    # print out the product info for products in cart
    #
    for product in products:
      print(product.product_id)
      print(" ", product.product_title)
      print(" ", product.product_price)
      # increment total price and total items
      total_price += product.product_price
      items += 1
    # print at the bottom of shopping cart list
    print(f"SUBTOTAL ({ items } items): ${ total_price }")
    return

  except Exception as e:
    logging.error("users() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# remove
#
def remove(baseurl):
  """
  Removes 

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # get user input:
    #
    print("Enter product id>")
    product_id = input()

    #
    # build message:
    #
    data = {"productid": product_id}

    #
    # call the web service:
    #
    api = '/remove'
    url = baseurl + api
    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      return

    #
    # deserialize and print message
    #
    body = res.json()
    msg = body
    print(msg)
    return

  except Exception as e:
    logging.error("reset() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# download
#
def download(baseurl):
  """
  Downloads all thumbnails in shopping cart as zip folder.

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
    api = '/download'
    url = baseurl + api

    res = requests.get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # if we get here, status code was 200, so we
    # have results to deserialize and display:
    #
    body = res.json()

    datastr = body

    base64_bytes = datastr.encode()
    bytes = base64.b64decode(base64_bytes)

    # writes bytes to files in destination folder "shopping_cart.zip" stored in current working directory
    with open("shopping_cart.zip", "wb") as f:
      f.write(bytes)

    return

  except Exception as e:
    logging.error("download() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
# main
#
try:
  print('** Welcome to IKEA **')
  print()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  #
  # what config file should we use for this session?
  #
  config_file = 'ikeaapp-client-config.ini'

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
      recommend(baseurl)
    elif cmd == 2:
      get_product_url(baseurl)
    elif cmd == 3:
      upload(baseurl)
    elif cmd == 4:
      list(baseurl)
    elif cmd == 5:
      remove(baseurl)
    elif cmd == 6:
      download(baseurl)
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** Hej! Thanks for visiting IKEA! **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
