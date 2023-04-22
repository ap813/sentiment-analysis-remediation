import boto3
import re
import json
import os
import base64

# Used to validate email
email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

# AWS clients to interact with services
comprehend = boto3.client('comprehend', region_name="us-west-2")
sns = boto3.client('sns', region_name="us-west-2")

# Validate request body
def validate_request(body):
    if not body['name']:
        return False
    email = body['email']
    if not email or not re.fullmatch(email_regex, email):
        return False
    if not body['review']:
        return False
    
    return True

# Wrapper for returning json response
def return_http_response(status_code, message):
    return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "Message": message
            })
        }

# Entry point for lambda call
def lambda_handler(event, context):
    # API Gateway proxy encodes this in base64
    if event.get('isBase64Encoded'):
        payload=base64.b64decode(event.get('body'))
    else:
        payload=event.get('body')

    # Convert the payload into a JSON Object
    body = json.loads(payload)
    if not validate_request(body):
        return return_http_response(400, "Invalid request body")
    
    # Do the sentiment analysis
    sentiment=comprehend.detect_sentiment(Text=body['review'],LanguageCode='en')['Sentiment']

    # When sentiment isn't negative, just return a 200
    if sentiment != 'NEGATIVE':
        return return_http_response(200, "Review not negative")
    
    # Sentiment was negative, publish to SNS 
    try:
        sns.publish(
            TopicArn=os.environ.get('topic_target_arn'),
            Message=json.dumps({
                "default": json.dumps({
                    "name": body['name'],
                    "email": body['email'],
                    "review": body['review']
                }),
            }),
            MessageStructure='json'
        )
    except Exception as ex:
        print("error publishing to SNS: ", ex)
        return return_http_response(500, "An error occurred")

    # Tell the caller that the review was negative and alerted upon
    return return_http_response(200, "Review was negative and was alerted upon")