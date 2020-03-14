import json
import boto3
import logging

def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
    
    
    response = client.post_text(
        botName='DiningConciergeBot',
        botAlias='DiningBot',
        userId='lf0',
        inputText=event["message"])
    return {
        'statusCode': 200,
        'body': response,
        "headers": { 
            "Access-Control-Allow-Origin": "*" 
        }
    }