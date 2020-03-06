import json
import boto3
import datetime
from botocore.vendored import requests
import csv
from decimal import Decimal

with open('merged.csv', newline='') as f:
    reader = csv.reader(f)
    restaurants = list(reader)
# print(type(int(restaurants[1][5][0])))
restaurants = restaurants[1:]

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')


for restaurant in restaurants:
    if restaurant[6] == '':
           print(restaurant[0])  
    tableEntry = {
        'id': restaurant[0],
        'name': restaurant[1],
        'address': restaurant[2],
        'coordinates': restaurant[3],
        'review_count': int(restaurant[4]),
        'rating': Decimal(restaurants[1][5]),
        'zip_code': restaurant[6],
        'cuisine': restaurant[7]
    }                

    table.put_item(
        Item={
            'insertedAtTimestamp': str(datetime.datetime.now()),
            'id': tableEntry['id'],
            'name': tableEntry['name'],
            'address': tableEntry['address'],
            'coordinates': tableEntry['coordinates'],
            'review_count': tableEntry['review_count'],
            'rating': tableEntry['rating'],
            'zip_code': tableEntry['zip_code'],
            'cuisine': tableEntry['cuisine']
           }
        )