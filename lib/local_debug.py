"""
Module to help with mocking/bypassing
RaspberryPi specific code to enable for
debugging on a Mac or Windows host.
"""

from sys import platform, version_info
from sys import platform as os_platform
import platform

REQUIRED_PYTHON_VERSION = 3.5
IS_LINUX = 'linux' in os_platform
DETECTED_CPU = platform.machine()
IS_PI = "arm" in DETECTED_CPU


def validate_python_version():
    """
    Checks to make sure that the correct version of Python is being used.

    Raises:
        Exception -- If the  version of Python is not new enough.
    """

    major_required_python_version = int(REQUIRED_PYTHON_VERSION)
    minor_required_python_version = int(
        (REQUIRED_PYTHON_VERSION - major_required_python_version) * 10)

    major_version_acceptable: bool = version_info.major >= major_required_python_version
    minor_version_acceptable: bool = version_info.minor >= minor_required_python_version
    python_version_acceptable: bool = major_version_acceptable and minor_version_acceptable

    error_text = 'Requires Python {}, found {}.{}'.format(
        REQUIRED_PYTHON_VERSION, version_info.major, version_info.minor)

    if not python_version_acceptable:
        print(error_text)
        raise Exception(error_text)


def is_debug():
    """
    returns True if this should be run as a local debug (Mac or Windows).
    """

    return os_platform in ["win32", "darwin"] or (IS_LINUX and not IS_PI)


validate_python_version()
