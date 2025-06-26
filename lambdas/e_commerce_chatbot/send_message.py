import json 
import os
from ast import literal_eval
import boto3

from shared.configs.logging_config import logger


lambda_client = boto3.client('lambda')

TARGET_LAMBDA = os.getenv('TARGET_LAMBDA')

if not TARGET_LAMBDA:
    raise ValueError("TARGET_LAMBDA environment variable is required")

def send_message_to_wpp(phone_number, message, instance):
    
    message_body = {
        "phone_number": phone_number,
        "instance": instance
    }
    
    if isinstance(message, str):
        try:
            message = literal_eval(message)
        except:
            message_body.update({
                "message_type": "text",
                "message_to_send": message
            })
            return send_to_wpp(message_body)

    if isinstance(message, dict) and "list_response" in message:
        message_body.update({
            "message_type": "list",
            **message["list_response"]
        })
    else:
        message_body.update({
            "message_type": "text",
            "message_to_send": message
        })

    return send_to_wpp(message_body)


def send_to_wpp(message_body):
    try:
        logger.info(f"Sending message to WPP for cellphone number [{message_body['phone_number']}] using instance [{message_body['instance']}]")
        
        payload = {"MessageBody": message_body, "MessageGroupId": message_body['phone_number']}
        
        
        response = lambda_client.invoke(
            FunctionName = TARGET_LAMBDA,
            InvocationType = "Event",
            Payload=json.dumps(payload)
        )
        
        logger.info("Message sent to post lambda")
        
        return response
    
    except Exception as e:
        logger.error(f"Error sending message to Lambda_Post: {str(e)}")
        return {
            "statusCode": 500,
            "body": f"Error sending message to Lambda_Post: {str(e)}"
        }