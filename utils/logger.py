import logging
from colorlog import ColoredFormatter

def setup_logger(log_level):

    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(getattr(logging, log_level))

        console_handler = logging.StreamHandler()
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)-8s%(reset)s %(white)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'bold_red',
                'CRITICAL': 'bold_purple',
                'DEBUG': 'cyan'
            },
            secondary_log_colors={},
            style='%'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger