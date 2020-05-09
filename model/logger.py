import logging
from sys import stdout as standard_output


class Logger:
    def __init__ (self):
        super().__init__(self)

    @staticmethod
    def create_logger (name: str, severity: int, to_file=False):
        logger = logging.getLogger(name)
        logger.setLevel(severity)

        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        format_date = '%d/%m/%Y %I:%M:%S %p'

        if to_file:
            handler = logging.FileHandler('server.log', 'w')
        else:
            handler = logging.StreamHandler(standard_output)
            format_string = '%(name)s: %(message)s'

        formatter = logging.Formatter(fmt=format_string, datefmt=format_date)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger
