import json

from lambdas.debouncer.send_message_api.configs.logging_config import logger
from message_sender import MessageSender


def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event))

    message_sender = MessageSender()

    
    message = event["MessageBody"]
    instance = message.pop('instance')
    phone_number = message.pop('phone_number')
    message_type = message.pop('message_type', 'text')
    message_content = message.pop('message_to_send', '')

    logger.info('Processing message for instance: %s, phone_number: %s', instance, phone_number)

    try:
        message_sender.send_message(
            message_type=message_type,
            phone_number=phone_number,
            instance=instance,
            message_to_send=message_content
        )
    except Exception as e:
        logger.error(f'Error sending message to {phone_number}: {str(e)}')

    return {
        'statusCode': 200,
        'body': json.dumps('Messages processed successfully')
    }
