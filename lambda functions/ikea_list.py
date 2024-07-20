#
# ikea_list
# Returns the contents of the client's shopping list and the subtotal.
#
import json
import boto3
import os
import datatier
from configparser import ConfigParser
from decimal import Decimal


def lambda_handler(event, context):
    try:
        print("**STARTING**")
        print("**lambda: ikeaapp_list**")

        # setup AWS based on config file:
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

        # open connection to the database:
        print("**Opening connection**")
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username,
                                     rds_pwd, rds_dbname)

        # retrieve all the products in shopping cart:
        print("**Retrieving data**")
        sql = "SELECT * FROM cart"
        rows = datatier.retrieve_all_rows(dbConn, sql)

        # convert all decimals to floats for compatibility with JSON
        new_rows = []
        for row in rows:
            new_row = list(row)
            for i, value in enumerate(new_row):
                if isinstance(value, Decimal):
                    new_row[i] = float(value)
            new_rows.append(new_row)

        for row in new_rows:
            print(row)

        # respond in an HTTP-like way, i.e., with a status code and body in JSON format:
        print("**DONE, returning rows**")
        return {'statusCode': 200, 'body': json.dumps(new_rows)}

    except Exception as err:
        # if error
        print("**ERROR**")
        print(str(err))
        return {'statusCode': 400, 'body': json.dumps(str(err))}
