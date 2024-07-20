import os
import boto3
import shutil
import json
import base64

from configparser import ConfigParser


def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: ikeaapp_download")
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
    s3_client = boto3.client('s3')

    # download all files from the specified folder in the S3 bucket
    response = s3_client.list_objects_v2(Bucket=bucketname,
                                         Prefix='ikeaapp/cart_ikeaapp')
    dir = "/tmp/cart_ikeaapp"

    if not os.path.exists(dir):
      os.makedirs(dir)

    print("**Downloading shopping cart from S3**")

    # check if any objects were found in the folder
    if 'Contents' in response:
      # iterate over each object in the folder
      for obj in response['Contents']:
        # get the object key (file name)
        obj_key = obj['Key']
        # define the local file path to save the object
        local_filename = f'/tmp/{obj_key[8:30]}'
        # download the object from S3 to the local file path
        bucket.download_file(obj_key, local_filename)

    print("DOWNLOAD DONE")

    # zip the downloaded files
    zip_filepath = '/tmp/cart_ikeaapp.zip'

    if os.path.exists(dir) and os.listdir(dir):
      # zip the downloaded files
      zip_filepath = '/tmp/cart_ikeaapp.zip'
      shutil.make_archive(zip_filepath[:-4], 'zip', dir)
      print("ZIP MADE")
    else:
      # if the directory doesn't exist or is empty, raise an error
      raise Exception(
          "directory '{}' either doesn't exist or is empty".format(dir))

    print("**Results:")

    #
    # open the file and read as raw bytes:
    #
    infile = open(zip_filepath, "rb")
    bytes = infile.read()
    infile.close()

    #
    # now encode the data as base64. Note b64encode returns
    # a bytes object, not a string. So then we have to convert
    # (decode) the bytes -> string, and then we can serialize
    # the string as JSON for download:
    #
    data = base64.b64encode(bytes)
    datastr = data.decode()

    print("**DONE, returning results**")

    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    return {'statusCode': 200, 'body': json.dumps(datastr)}

  except Exception as err:
    # if error
    print("**ERROR**")
    print(str(err))

    return {'statusCode': 400, 'body': json.dumps(str(err))}
