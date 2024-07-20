#
# ikea_get_product_url
# client enters the product ID, and the server returns a link to the product
#

import json
import os
import datatier

from configparser import ConfigParser


def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: ikeaapp-get-url**")

    #
    # setup AWS based on config file:
    #
    config_file = 'ikeaapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file

    configur = ConfigParser()
    configur.read(config_file)

    # configure for RDS access
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    if "body" not in event:
      raise Exception("event has no body")

    body = json.loads(event["body"])  # parse the json

    # check for parameters
    if "product_id" not in body:
      raise Exception("event has a body but no product_id")

    product_id = body["product_id"]

    #
    # open connection to the database:
    #
    print("**Opening connection**")

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username,
                                 rds_pwd, rds_dbname)

    # initialize product_url
    product_url = ""

    # sql to get url from product ID
    sql = "SELECT product_url FROM products WHERE product_id = %s"

    row = datatier.retrieve_all_rows(dbConn, sql, [product_id])

    # assign product_url to what we got back
    product_url = str(row[0])

    return {'statusCode': 200, 'body': json.dumps(product_url)}

  except Exception as err:
    # if error
    print("**ERROR**")
    print(str(err))

    return {'statusCode': 400, 'body': json.dumps(str(err))}
