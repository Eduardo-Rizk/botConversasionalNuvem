import json
import boto3
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
PROCESSING_LAMBDA_FUNCTION = os.environ['PROCESSING_LAMBDA_FUNCTION']

# Set up DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


def invoke_lambda(instance_name, cellphone_number, message, last_update):
    """Invoke another Lambda function to process the message."""
    lambda_client = boto3.client('lambda')
    payload = {
        'instance': instance_name,
        'phone_number': cellphone_number,
        'message': message,
        'last_update': last_update
    }

    if not PROCESSING_LAMBDA_FUNCTION:
        logger.error(f'No processing Lambda configured for instance_name {instance_name}')
        return

    try:
        response = lambda_client.invoke(
            FunctionName=PROCESSING_LAMBDA_FUNCTION,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        logger.info(f'Invoked Lambda for instance_name {instance_name} with response: {response}')
    except Exception as e:
        logger.error(f'Failed to invoke Lambda for instance_name {instance_name}: {str(e)}')


def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event))

    instance_name = event['instance_name']
    cellphone_number = event['cellphone_number']
    message = event['message']
    last_update = event['last_update']

    # Double-check if the message is still the most recent one
    response = table.get_item(Key={'instance_name': instance_name, 'cellphone_number': cellphone_number})

    if 'Item' not in response or response['Item']['last_update'] != last_update:
        logger.info('Message was updated, skipping processing for %s', cellphone_number)
        return {
            'statusCode': 200,
            'body': json.dumps('Message was updated, skipping processing')
        }

    logger.info('Processing message: %s', message)

    invoke_lambda(instance_name, cellphone_number, message, last_update)

    # After sending, delete the message from DynamoDB
    try:
        table.delete_item(Key={'instance_name': instance_name, 'cellphone_number': cellphone_number})
        logger.info('Message from app %s and phone number %s processed and deleted from DynamoDB', instance_name,
                    cellphone_number)
    except Exception as e:
        logger.error(f'Failed to delete item for app {instance_name} and phone number {cellphone_number}: {str(e)}')

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }
