#
# ikea_upload
#
# Uploads a JPG/JPEG image of the client's desired product from their local environment
# to S3 bucket under the desired product ID -> ikea_compute then turns this image into
# a PNG thumbnail stored in the shopping cart folder in the bucket
#

import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier

from configparser import ConfigParser


def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: ikeaapp_upload**")

    #
    # setup AWS based on config file:
    #
    config_file = 'ikeaapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file

    configur = ConfigParser()
    configur.read(config_file)

    #
    # configure for S3 access:
    #
    s3_profile = 's3readwrite'
    boto3.setup_default_session(profile_name=s3_profile)

    bucketname = configur.get('s3', 'bucket_name')

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketname)

    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    #
    # the user has sent us three parameters:
    #  1. product id
    #  2. filename of their file
    #  3. raw file data in base64 encoded string
    #
    # The parameters are coming through web server
    # (or API Gateway) in the body of the request
    # in JSON format.
    #
    print("**Accessing request body**")

    if "body" not in event:
      raise Exception("event has no body")

    body = json.loads(event["body"])  # parse the json

    # check for parameters
    if "productid" not in body:
      raise Exception("event has a body but no productid")
    if "filename" not in body:
      raise Exception("event has a body but no filename")
    if "data" not in body:
      raise Exception("event has a body but no data")

    productid = body["productid"]
    filename = body["filename"]
    datastr = body["data"]

    #
    # key to store original file as when downloaded
    #
    key = "ikeaapp/" + str(productid) + ".jpg"

    print("productid:", productid)

    #
    # open connection to the database:
    #
    print("**Opening connection**")

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username,
                                 rds_pwd, rds_dbname)

    #
    # make sure the productid is valid:
    #
    print("**Checking if productid is valid**")

    sql = "SELECT * FROM products WHERE product_id = %s;"

    row = datatier.retrieve_one_row(dbConn, sql, [productid])

    if row == ():  # no such product
      print("**No such product, returning...**")
      return {'statusCode': 400, 'body': json.dumps("no such product...")}

    print(row)
    productname = row[1]
    price = row[6]
    producturl = row[2]

    #
    # at this point the product exists, so safe to upload to S3:
    #
    base64_bytes = datastr.encode()  # string -> base64 bytes
    bytes = base64.b64decode(base64_bytes)  # base64 bytes -> raw bytes

    #
    # write raw bytes to local filesystem for upload:
    #
    print("**Writing local data file**")
    #
    # Writes binary file to local directory,
    # write the bytes we received from the client, and
    # close the file.
    #
    local_filename = "/tmp/data.jpg"
    #
    #
    outfile = open(local_filename, "wb")
    outfile.write(bytes)
    outfile.close()

    #
    # generate unique filename in preparation for the S3 upload:
    #
    print("**Uploading local file to S3**")

    basename = pathlib.Path(filename).stem
    extension = pathlib.Path(filename).suffix

    # filename for upload must be jpg/jpeg
    if extension != ".jpg" and extension != ".jpeg":
      raise Exception("expecting filename to have .jpg or .jpeg extension")

    print("S3 bucketkey:", key)

    #
    # adds product id of product image that client is
    # uploading to shopping cart
    #
    print("**Adding cart row to database**")

    sql = """
      INSERT INTO cart(product_id, product_name, price)
                  VALUES(%s, %s, %s);
    """

    datatier.perform_action(dbConn, sql, [productid, productname, price])

    #
    # now that DB is updated, let's upload image to S3:
    #
    print("**Uploading data file to S3**")

    #
    # uploads image
    #
    bucket.upload_file(local_filename,
                       key,
                       ExtraArgs={
                           'ACL': 'public-read',
                           'ContentType': 'image/jpg'
                       })

    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning jobid**")

    return {'statusCode': 200, 'body': json.dumps(producturl)}

  except Exception as err:
    # if error
    print("**ERROR**")
    print(str(err))

    return {'statusCode': 400, 'body': json.dumps(str(err))}
