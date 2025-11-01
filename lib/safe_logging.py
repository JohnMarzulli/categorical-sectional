"""
Logging utilities for the WeatherMap
"""

import contextlib
import traceback
from datetime import datetime

from lib.logger import LOGGER

TAB_TEXT = " " * 4
MODULE_NAME = "<module>"


def __get_callstack_indent_count__(stack_adjustment: int = 3) -> int:
    """
    Returns the number of indents that should be applied to the logging statement.

    Keyword Arguments:
        stack_adjustment {int -- The number of frames down the ACTUAL function name is. (default: {3})

    Returns:
        int -- The number of indents.
    """

    try:
        cs_info = traceback.extract_stack()

        indents = 0

        for index in range(len(cs_info) - stack_adjustment, 0, -1):
            if MODULE_NAME in cs_info[index].name:
                break
            else:
                indents += 1

        if indents < 0:
            indents = 0

        return indents
    except Exception:
        return 0


def __get_indents__(count: int = 0, stack_adjustment: int = 3) -> str:
    """
    Returns whitespace for the number of given indents.

    Keyword Arguments:
        count {int} -- The number of indents to return whitespace for. (default: {0})
        stack_adjustment {int -- The number of frames down the ACTUAL function name is. (default: {3})

    Returns:
        string -- A whitespace string.
    """

    count = max(count, 0)
    function_name = "UNKNOWN"
    line_num = "UNKNOWN"

    with contextlib.suppress(Exception):
        cs_info = traceback.extract_stack()
        index = len(cs_info) - stack_adjustment
        function_name = f"{cs_info[index].name}()"

        if MODULE_NAME in function_name:
            function_name = cs_info[index].filename

        line_num = cs_info[index].lineno
    return f"{TAB_TEXT * count}{function_name}:{line_num}: "


def safe_log(message: str):
    """
    Logs an INFO level message safely. Also prints it to the screen.

    Arguments:
        logger {logger} -- The logger to use.
        message {string} -- The message to log.
    """

    try:
        indents = __get_indents__(__get_callstack_indent_count__())
        if LOGGER is not None:
            LOGGER.log_info_message(indents + message)
        else:
            print(f"{datetime.now()} INFO: {indents}{message}")
    except Exception:
        print(f"{indents}{message}")


def safe_log_warning(message: str):
    """
    Logs a WARN level message safely. Also prints it to the screen.

    Arguments:
        logger {logger} -- The logger to use.
        message {string} -- The message to log.
    """

    try:
        indents = __get_indents__(__get_callstack_indent_count__())

        if LOGGER is not None:
            LOGGER.log_warning_message(indents + message)
        else:
            print(f"{datetime.now()} WARN: {indents}{message}")
    except Exception:
        print(f"{indents}{message}")
