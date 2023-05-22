import logging
from colorlog import ColoredFormatter

def setup_logger(logger_name=None):
    logger_name = logger_name or __name__
    
    # Create a logger
    logger = logging.getLogger(logger_name)

    # Set the log level to DEBUG to capture all the logs
    logger.setLevel(logging.INFO)

    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Define log colors
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }

    # Define the log format
    log_format = "%(log_color)s[%(levelname)s] %(asctime)s - %(message)s%(reset)s"

    # Create a formatter
    formatter = ColoredFormatter(log_format, log_colors=log_colors)

    # Add formatter to console handler
    ch.setFormatter(formatter)

    # Add console handler to logger
    logger.addHandler(ch)

    return logger