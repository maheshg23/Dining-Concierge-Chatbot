"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
SQS = boto3.client("sqs")

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

def getQueueURL():
    """Retrieve the URL for the configured queue name"""
    q = SQS.get_queue_url(QueueName='DiningConciergeSQS').get('QueueUrl')
    return q
    
def record(event):
    """The lambda handler"""
    logger.debug("Recording with event %s", event)
    data = event.get('data')
    try:
        logger.debug("Recording %s", data)
        u = getQueueURL()
        logging.debug("Got queue URL %s", u)
        resp = SQS.send_message(
            QueueUrl=u, 
            MessageBody="Dining Concierge message from LF1 ",
            MessageAttributes={
                "Location": {
                    "StringValue": str(get_slots(event)["Location"]),
                    "DataType": "String"
                },
                "Cuisine": {
                    "StringValue": str(get_slots(event)["Cuisine"]),
                    "DataType": "String"
                },
                "Date" : {
                    "StringValue": get_slots(event)["Date"],
                    "DataType": "String"
                },
                "Time" : {
                    "StringValue": str(get_slots(event)["Time"]),
                    "DataType": "String"
                },
                "NumPeople" : {
                    "StringValue": str(get_slots(event)["NumberOfPeople"]),
                    "DataType": "String"
                },
                "PhoneNum" : {
                    "StringValue": str(get_slots(event)["PhoneNumber"]),
                    "DataType": "String"
                }
            }
        )
        logger.debug("Send result: %s", resp)
    except Exception as e:
        raise Exception("Could not record link! %s" % e)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """
def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_dining_suggestion(location, cuisine, time, date, numberOfPeople, phoneNumber):
    locations = ['manhattan', 'new york']
    if location is not None and location.lower() not in locations:
        return build_validation_result(False,
                                       'Location',
                                       'We do not have suggestions for {}, would you like suggestions for a differenet location?  '
                                       'Our most popular location is Manhattan '.format(location))
                                       
    cuisines = ['chinese', 'indian', 'italian', 'japanese', 'mexican', 'thai', 'korean', 'arab', 'american']
    if cuisine is not None and cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'Cuisine',
                                       'We do not have suggestions for {}, would you like suggestions for a differenet cuisine ?  '
                                       'Our most popular Cuisine is Indian '.format(cuisine))
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand that, what date would you like to have the recommendation for?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date',  'Sorry, that is not possible What day would you like to have the recommendation for?')
            
    
    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', None)

        if hour < 10 or hour > 24:
            # Outside of business hours
            return build_validation_result(False, 'Time', 'Our business hours are from 10 AM. to 11 PM. Can you specify a time during this range?')
    
    if numberOfPeople is not None and not numberOfPeople.isnumeric():
        return build_validation_result(False,
                                       'NumberOfPeople',
                                       'That does not look like a valid number {}, '
                                       'Could you please repeat?'.format(numberOfPeople))
    
    if phoneNumber is not None and not phoneNumber.isnumeric():
        return build_validation_result(False,
                                       'PhoneNumber',
                                       'That does not look like a valid number {}, '
                                       'Could you please repeat? '.format(phoneNumber))    
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def diningSuggestions(intent_request,context):
    

    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    date = get_slots(intent_request)["Date"]
    time = get_slots(intent_request)["Time"]
    numberOfPeople = get_slots(intent_request)["NumberOfPeople"]
    phoneNumber = get_slots(intent_request)["PhoneNumber"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_dining_suggestion(location, cuisine, time, date, numberOfPeople, phoneNumber)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.
    
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        return delegate(output_session_attributes, get_slots(intent_request))

    record(intent_request)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thank you for the information, we are generating our recommendations, we will send the recommendations to your phone when they are generated'})


""" --- Intents --- """

def welcome(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Hey there, How may I serve you today?'})

def thankYou(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'My pleasure, Have a great day!!'})


def dispatch(intent_request,context):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return diningSuggestions(intent_request,context)
    elif intent_name == 'ThankYouIntent':
        return thankYou(intent_request)
    elif intent_name == 'WelcomeIntent':
        return welcome(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event,context)
