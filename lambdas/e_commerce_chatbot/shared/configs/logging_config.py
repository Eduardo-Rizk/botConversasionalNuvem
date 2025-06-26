import logging


def setup_logger():
    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


logger = setup_logger()
