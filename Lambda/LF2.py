import json
import boto3
from botocore.exceptions import ClientError
from elasticsearch import Elasticsearch, RequestsHttpConnection
from boto3.dynamodb.conditions import Key, Attr
import random

def lambda_handler(event, context):
    sqsclient = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/239255194144/restaurantQueue'

    # Receive message from SQS queue
    response = sqsclient.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SequenceNumber'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=1
    )
    
    if 'Messages' in response:
        es_endpoint = 'search-restaurants-bpoued5hlvrv4fn74iuqwi7i7y.us-east-1.es.amazonaws.com' 
        
        es = Elasticsearch(
            hosts = [{'host': es_endpoint, 'port': 443}],
            use_ssl = True,
            verify_certs = True,
            connection_class = RequestsHttpConnection
        )

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('yelp-restaurants')

        for message in response['Messages']:
            receipt_handle = message['ReceiptHandle']
            req_attributes = message['MessageAttributes']
            print req_attributes

            # Get the food category from queue message attributes.
            index_category = req_attributes['Categories']['StringValue']

            searchData = es.search(index="restaurants", body={
                                        "query": {
                                        "match": {
                                        "categories.title": index_category
                                        }}})

            restaurantIds = []
            for hit in searchData['hits']['hits']:
                restaurantIds.append(hit['_source']['id'])

            randomRestaurantIds = random.sample(restaurantIds, k=3)

            getEmailContent = getDynamoDbData(table, req_attributes, randomRestaurantIds)
            #print "DynamoDB Query ResponseData" + resultData 

            # send the email
            sendMailToUser(req_attributes, getEmailContent)

            sqsclient.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            
            print searchData['hits']['total']


    else:
        return {
        'statusCode': 500,
        'body': json.dumps('Error fetching data from the queue.')
    }
    
    return {
        'statusCode': 200,
        'body': response
    }

def getDynamoDbData(table, requestData, businessIds):
    if len(businessIds) <= 0:
        return 'We can not find any restaurant under this description, please try again.'

    textString = "Hello! Here are my " + requestData['Categories']['StringValue'] + " restaurant suggestions for " + requestData['PeopleNum']['StringValue'] +" people, for " + requestData['DiningDate']['StringValue'] + " at " + requestData['DiningTime']['StringValue'] + ":"
    count = 1
    
    for business in businessIds:
        responseData = table.query(KeyConditionExpression=Key('id').eq(business))
        if responseData and len(responseData['Items']) >= 1:
            print responseData
            responseData = responseData['Items'][0]
            address = responseData['address'] 
            textString = textString + ", " + str(count) + ". " + str(responseData['name']) + ", located at " + str(address[0]) + " " + str(address[1])
            count+=1
    return textString

def sendMailToUser(requestData, content):
    
    SENDER = "lolneelsd@gmail.com"
    RECIPIENT = requestData['EmailId']['StringValue']
    AWS_REGION = "us-east-1"
    
    
    BODY_TEXT = content   
    
    # Create a new SES resource and specify a region.
    ses = boto3.client('ses',region_name=AWS_REGION)
    
    # return true
    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = ses.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Data': json.dumps(BODY_TEXT),
                    },
                },
                'Subject': {
                    'Data': "Your Dining Suggestions",
                }
            },
            Source=SENDER,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])