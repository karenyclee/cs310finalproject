#
# ikea_compute
#
# event-driven lambda function that shrinks image to PNG thumbnail after
# JPG/JPEG image is dropped into S3
#
# need to create python 3.8 lambda function
# add a layer
#     -> Specify an ARN
#     -> arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p38-Pillow:10
# https://api.klayers.cloud/api/v2/p3.8/layers/latest/us-east-2/json

# upload a .JPG or .JPEG file to bucket from client-side,
# shrinks image into .PNG format, puts it in shopping cart folder of bucket

import boto3
import io
import struct
import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier
import urllib.parse
import string
from PIL import Image

from configparser import ConfigParser


def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: ikeaapp_compute**")

    #
    # in case we get an exception, initial this filename
    # so we can write an error message if need be:
    #
    bucketkey_results_file = ""

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
    # this function is event-driven by a JPG/JPEG being
    # dropped into S3. The bucket key is sent to
    # us and obtain as follows:
    #
    bucketkey = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print("bucketkey:", bucketkey)

    # checks that bucket item added has suffix ".jpeg" or ".jpg"
    extension = pathlib.Path(bucketkey).suffix
    if extension != ".jpg" and extension != ".jpeg":
      raise Exception("expecting S3 document to have .jpg or .jpeg extension")

    # creates empty results file for thumbnail storage (stored in bucket/ikeaapp/cart_ikeaapp/imgname)
    if extension == ".jpg":
      bucketkey_results_file = str("ikeaapp/" + "cart_" + bucketkey[0:-4] +
                                   ".PNG")
    else:
      bucketkey_results_file = str("ikeaapp/" + "cart_" + bucketkey[0:-5] +
                                   ".PNG")

    local_jpg = str("/tmp/data" + extension)
    bucket.download_file(bucketkey, local_jpg)

    print('local jpg before: ', local_jpg)

    image = Image.open(local_jpg)

    # resize image
    image.thumbnail((50, 50))
    print('image: ', image)

    print('local jpg after: ', local_jpg)

    resized_buffer = io.BytesIO()

    # thumbnail saved with .PNG format to avoid neverending recursion
    image.save(resized_buffer, format='PNG')
    resized_buffer.seek(0)
    print("local results file:", resized_buffer)

    print("bucketkey results file:", bucketkey_results_file)

    # uploads thumbnail to cart_ikeaapp bucket
    bucket.upload_fileobj(resized_buffer,
                          bucketkey_results_file,
                          ExtraArgs={
                              'ACL': 'public-read',
                              'ContentType': 'image/PNG'
                          })

    print("**DONE, returning success**")

    return {'statusCode': 200, 'body': json.dumps("success")}

  except Exception as e:
    # if error
    print(f"Error processing image: {str(e)}")
    return {'statusCode': 500, 'body': f"Error processing image: {str(e)}"}
