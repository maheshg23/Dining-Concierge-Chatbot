from __future__ import print_function

import argparse
import json
import pprint
import requests
import sys
import urllib
import boto3
import decimal
import csv

try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode


API_KEY= '94-YVSzhfWpz8gsYO_l8aVV17p7eRMQq1LmUqsjb1Ybfu-lG-LtLf01x2Kv3NpWdHCmsZXK482N9oiXiw8gw6hcJpNMEyyBpeEfv7AKrMnq9f4JKqb6K8tM_DeFNXnYx' 

API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.


# Defaults for our simple example.
#chinese, indian, italian, japanese, mexican, thai, korean
DEFAULT_TERM = 'korean restaurants'
DEFAULT_LOCATION = 'Manhattan'
SEARCH_LIMIT = 50
# OFFSET = 150


def request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    print(u'Querying {0} ...'.format(url))
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()


def search(api_key, term, location, offSet):

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
         'offset': offSet,
         'limit': SEARCH_LIMIT        
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

def getTotal(api_key, term, location):

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
         #'offset': offSet,
         'limit': SEARCH_LIMIT        
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params).get('total')


def get_business(api_key, business_id):
    """Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id
    return request(API_HOST, business_path, api_key)


def query_api(term, location):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    list1 = []
    list1.append("bID")
    list1.append("name")
    list1.append("address")
    list1.append("cord")
    list1.append("numOfReview")
    list1.append("rating")
    list1.append("zipcode")
    list1.append("cuisine")
    filename = "Restaurants"+ '.csv'
    with open(filename, "a", newline='') as fp:
        wr = csv.writer(fp, dialect='excel')
        wr.writerow(list1)

    # cuisines = ['chinese', 'indian', 'italian', 'japanese', 'mexican', 'thai', 'korean', 'arab', 'american']
    cuisines = ['chinese', 'indian', 'italian', 'japanese', 'american']
    for cuisine in cuisines:
        newterm = cuisine+ ' restaurants'
        total = getTotal(API_KEY, newterm, location)
        print(total, cuisine)
        run = 0
        maxOffSet = int(total / 50)
        businesses = []
        for offSet in range(0, maxOffSet+1):
            if run == 25:
                break
            response = search(API_KEY, newterm, location, offSet*50)
            if response.get('businesses') is None:
                break
            businesses.append(response.get('businesses'))
            run+=1

        printVar = []
        for buis in businesses:
            for b in buis:
                printVar.append(b)

        if not businesses:
            # print(u'No businesses for {0} in {1} found.'.format(term, location))
            return

        # list1 = []
        # list1.append("bID")
        # list1.append("name")
        # list1.append("address")
        # list1.append("cord")
        # list1.append("numOfReview")
        # list1.append("rating")
        # list1.append("zipcode")
        # list1.append("cuisine")
        # filename = cuisine+ '.csv'
        # with open(filename, "a", newline='') as fp:
        #         wr = csv.writer(fp, dialect='excel')
        #         wr.writerow(list1)
        
        for b in printVar:
            bID = b['id']
            name = b['name']
            add = ', '.join(b['location']['display_address'])
            numOfReview = int(b['review_count'])
            rating = float(b['rating'])

            if (b['coordinates'] and b['coordinates']['latitude'] and b['coordinates']['longitude']):
                cord = str(b['coordinates']['latitude'])+ ', '+str(b['coordinates']['longitude'])
            else:
                cord = None

            if (b['location']['zip_code']):
                zipcode = b['location']['zip_code']
            else:
                zipcode = None

            temparr = []
            temparr.append(bID)
            temparr.append(name)
            temparr.append(add)
            temparr.append(cord)
            temparr.append(numOfReview)
            temparr.append(rating)
            temparr.append(zipcode)
            temparr.append(cuisine)

            with open(filename, "a", newline='') as fp:
                wr = csv.writer(fp, dialect='excel')
                wr.writerow(temparr)

        print("Added ",cuisine," restaurants")



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM,
                        type=str, help='Search term (default: %(default)s)')
    parser.add_argument('-l', '--location', dest='location',
                        default=DEFAULT_LOCATION, type=str,
                        help='Search location (default: %(default)s)')

    input_values = parser.parse_args()

    try:
        query_api(input_values.term, input_values.location)
    except HTTPError as error:
        sys.exit(
            'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                error.code,
                error.url,
                error.read(),
            )
        )


if __name__ == '__main__':
    main()