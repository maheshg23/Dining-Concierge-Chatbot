import json
from datetime import *
import boto3

def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
    
    user_message = event["message"]
    user_id = event["userId"]
    lex_bot = 'DiningConcierge'
    bot_alias = 'lexLuthor'
        
    response = client.post_text(
        botName = lex_bot,
        botAlias = bot_alias,
        userId = user_id,
        inputText = user_message
    )   
    
    #return_msg = response
    """ response = {
                'text': return_msg
            } """
    
    return {
        'statusCode': 200,
        'headers': { 
            "Access-Control-Allow-Origin": "*" 
        },
        'body': json.dumps(response['message'])
    }