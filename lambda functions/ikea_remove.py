#
# remove
# Client inputs a product ID, and that item is deleted from their
# shopping cart.
#

import json
import boto3
import os
import datatier

from configparser import ConfigParser


def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: ikea_remove**")

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
    #
    bucketname = configur.get('s3', 'bucket_name')
    #
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

    if "body" not in event:
      raise Exception("event has no body")

    body = json.loads(event["body"])  # parse the json

    # check for parameters
    if "productid" not in body:
      raise Exception("event has a body but no productid")

    product_id = body['productid']

    print("**Opening connection**")

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username,
                                 rds_pwd, rds_dbname)

    #
    # first we need to make sure the productid is valid:
    #
    print("**Checking if productid is valid**")

    sql = "SELECT * FROM cart WHERE product_id = %s;"

    row = datatier.retrieve_one_row(dbConn, sql, [product_id])

    if row == ():  # no such product
      print("**No such product in cart, returning...**")
      return {
          'statusCode': 400,
          'body': json.dumps("no such product in cart...")
      }

    print("**Removing cart row to database**")

    # sql to delete row from cart table
    sql = """
            DELETE FROM cart WHERE product_id = %s
    """

    # execute the sql above
    datatier.perform_action(dbConn, sql, [product_id])

    #
    # now that DB is updated, let's remove image from S3:
    #
    print("**Removing image from S3**")
    # remove PNG from s3 bucket
    key = "ikeaapp/cart_ikeaapp/" + str(product_id) + ".PNG"

    try:
      bucket.delete_objects(Delete={'Objects': [{'Key': key}]})
      return {
          'statusCode':
          200,
          'body':
          json.dumps(
              f'Product {product_id} removed successfully from the shopping cart'
          )
      }
    except Exception as e:
      # if error
      return {'statusCode': 400, 'body': json.dumps(str(e))}

  except Exception as err:
    # if error
    print("**ERROR**")
    print(str(err))

    return {'statusCode': 400, 'body': json.dumps(str(err))}
