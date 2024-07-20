#
# recommend
# Client enters keywords for the product they are looking for (i.e.
# black office chair). Then, they enter the maximum price that they
# are comfortable with paying. The server looks for the products that
# are the best match (contain the keywords and are within budget) and
# the client app would return a list of product IDS and URLs to the
# products (capped at 5, but the client can request to see more
# recommendations if they want; these recommendations are sorted by
# how much it matches with the client search).
#

import json
import os
import datatier

from configparser import ConfigParser


def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: ikea_recommend**")

    #
    # setup AWS based on config file:
    #
    config_file = 'ikeaapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file

    configur = ConfigParser()
    configur.read(config_file)

    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    # checks for parameters
    if "body" not in event:
      raise Exception("event has no body")

    body = json.loads(event["body"])  # parse the json

    if "search" not in body:
      raise Exception("event has a body but no search")

    if "budget" not in body:
      raise Exception("event has a body but no budget")

    search = body["search"]
    budget = float(body["budget"])

    #
    # open connection to the database:
    #
    print("**Opening connection**")

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username,
                                 rds_pwd, rds_dbname)
    sql = "SELECT * FROM products WHERE product_price <= %s AND LOWER(product_title) LIKE %s"

    # ans dictionary stores IDs of products (key) and a dictionary of product_url and number of matches with search (value)
    ans = {}
    raw_keywords = search.split()
    keywords = [word.lower() for word in raw_keywords]

    # iterates over all search words to update match score
    for keyword in keywords:
      rows = datatier.retrieve_all_rows(dbConn, sql,
                                        [budget, "%" + keyword + "%"])
      # iterates over all products to see what matches with search word and updates ans dict
      for row in rows:
        product_id = row[0]
        product_url = row[2]
        if product_id in ans:
          ans[product_id]['score'] += 1
        else:
          ans[product_id] = {'url': product_url, 'score': 1}

    # sort the results by relevance (score)
    sort = sorted(ans.items(), key=lambda item: item[1]['score'], reverse=True)

    # formats response into dictionary form
    response = [{
        "product_id": product_id,
        "product_url": desc['url']
    } for product_id, desc in sort]

    return {'statusCode': 200, 'body': json.dumps(response)}

  except Exception as err:
    # if error
    print("**ERROR**")
    print(str(err))

    return {'statusCode': 400, 'body': json.dumps(str(err))}
