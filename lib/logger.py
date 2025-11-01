"""
Simple wrapper around a logger.
"""

import logging
import logging.handlers
import threading
from datetime import datetime, timezone

LOG_NAME = "weathermap"

__lock__ = threading.Lock()


def __escape__(text):
    """
    Replaces escape sequences do they can be printed.

    Funny story. PyDoc can't unit test strings with a CR or LF...
    It gives a white space error.

    >>> __escape__("text")
    'text'
    >>> __escape__("")
    ''
    """

    return str(text).replace("\r", "\\r").replace("\n", "\\n").replace("\x1a", "\\x1a")


class Logger:
    """
    Wrapper around a normal logger so stuff gets printed too.
    """

    def info(self, message_to_log):
        self.log_info_message(message_to_log, True)

    def warn(self, message_to_log):
        self.log_warning_message(message_to_log)

    def log_info_message(self, message_to_log, print_to_screen=True):
        """Log and print at Info level"""
        try:
            __lock__.acquire()

            if print_to_screen:
                text = (
                    f"{datetime.now(timezone.utc)} INFO: {__escape__(message_to_log)}"
                )
                print(text)
            self.__logger__.info(__escape__(message_to_log))
        finally:
            __lock__.release()

        return message_to_log

    def log_warning_message(self, message_to_log):
        """Log and print at Warning level"""
        try:
            __lock__.acquire()

            text = f"{datetime.now(timezone.utc)} WARN: {message_to_log}"
            self.__logger__.warning(__escape__(text))
        finally:
            __lock__.release()

        return message_to_log

    def __init__(self, logger):
        self.__logger__ = logger


__python_logger__ = logging.getLogger(LOG_NAME)
__python_logger__.setLevel(logging.DEBUG)
__handler__ = logging.handlers.RotatingFileHandler(
    "weathermap.log", maxBytes=10485760, backupCount=10
)
__handler__.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
__python_logger__.addHandler(__handler__)

LOGGER = Logger(__python_logger__)
