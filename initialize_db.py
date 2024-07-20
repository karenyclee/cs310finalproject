#
# Initializes products table in ikeaapp database through client-RDS
# interaction. IKEA would be the client wanting to modify RDS 
# by adding its products.
#
# Authors:
#   BHAVI BARNWAL, KAREN LEE
#   Northwestern University
#   Spring 2024
#

import datatier  # MySQL database access
import json
import sys

from configparser import ConfigParser

configur = ConfigParser()
configur.read('ikeaapp-config.ini')
endpoint = configur.get('rds', 'endpoint')
portnum = int(configur.get('rds', 'port_number'))
username = configur.get('rds', 'user_name')
pwd = configur.get('rds', 'user_pwd')
dbname = configur.get('rds', 'db_name')

dbConn = datatier.get_dbConn(endpoint, portnum, username, pwd, dbname)

if dbConn is None:
  print('**ERROR: unable to connect to database, exiting')
  sys.exit(0)

with open('ikea_sample_file.json', 'r') as file:
    products = json.load(file)

sql = """INSERT IGNORE INTO products 
    (product_title, product_url, sku, mpn, currency, product_price, product_condition, 
    available, seller, seller_url, brand) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

for product in products:
    try:
        print("Inserting product:", product['product_title'])
        datatier.perform_action(dbConn, sql, [
        product['product_title'],
        product['product_url'],
        product['sku'],
        product['mpn'],
        product['currency'],
        product['product_price'],
        product['product_condition'],
        product['availability'],
        product['seller'],
        product['seller_url'],
        product['brand']])
    except Exception as e:
        print(f"Failed to insert product: {product['product_title']}")
        print("Error:", e)
        
dbConn.close()
 
 
 
