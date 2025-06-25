import re
from typing import List

from shared.configs.logging_config import logger


def validate_event(event, required_fields: List):
    """Validate that the event contains the required data."""
    missing = [field for field in required_fields if field not in event]
    if missing:
        logger.warning(f"Validation failed: Missing fields - {missing}")
        return {"statusCode": 400, "body": f"Missing fields: {', '.join(missing)}"}
    return None


def split_message(message: str) -> list:
    return [part.strip() for part in message.split("\n\n") if part.strip()]


def bold_correction(message: str) -> str:
    """
    Converte negrito em formato Markdown (**texto**) para o formato do WhatsApp (*texto*).
    """
    return re.sub(r'\*\*(.*?)\*\*', r'*\1*', message)
