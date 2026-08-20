"""
Handles fetching and decoding weather.
"""

# Airports data can be sourced from https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/
# using the APT link, then using APT_BASE.csv
#
# It can be more directly sourced from https://ourairports.com/countries/US/airports.csv

import os
import re
import urllib.request
from datetime import datetime, timezone

import requests

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")))

from lib.cache import Cache, CacheResult
from lib.safe_logging import safe_log, safe_log_warning
from meteorology.types.metar import Metar

__rest_session__ = requests.Session()
__metar_report_cache__: Cache = Cache()
__station_last_called__ = {}

DEFAULT_READ_SECONDS = 15
DEFAULT_METAR_LIFESPAN_MINUTES = 60
DEFAULT_METAR_INVALIDATE_MINUTES = DEFAULT_METAR_LIFESPAN_MINUTES * 1.5


def get_metar(airport_icao_code: str) -> Metar:
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_icao_code {string} -- The ICAO code for the weather station.
    """

    metars = get_metars([airport_icao_code])

    return metars[airport_icao_code]


def get_metars(airport_icao_codes: list) -> dict:
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_icao_code {string} -- The list of ICAO code for the weather station.

    Returns:
        dictionary - A dictionary (keyed by airport code) of the RAW metars that were retrieved.
        An entry will be missing if the METAR could not be retrieved for that station.
    """

    metars: dict = __get_cached_metars__(airport_icao_codes)

    # First determine which stations we can make a METAR call for.
    # From those that are already in the cache, use those as a starting point.
    # If a new result is returned, merge that back into the results AND update the cache
    # in order to reduce call counts.
    #
    # The NOAA API call limits to something around 100 calls per minute (which we should be we below)
    metars_to_fetch: list = [ident for ident
                             in airport_icao_codes
                             if __is_station_ok_to_call__(ident)
                             or (not ident in metars)]
    fetched_metars: dict = __get_metar_reports_from_web__(metars_to_fetch)

    for identifier, new_metar in fetched_metars.items():
        __metar_report_cache__.set(identifier, new_metar)
        metars[identifier] = new_metar

    return metars


def __extract_metar_from_html_line__(raw_metar_line):
    """
    Takes a raw line of HTML from the METAR report and extracts the METAR from it.
    NOTE: A "$" at the end of the line indicates a "maintenance check" and is part of the report.

    Arguments:
        metar {string} -- The raw HTML line that may include BReaks and other HTML elements.

    Returns:
        string -- The extracted METAR.
    """

    metar = re.sub("<[^<]+?>", "", raw_metar_line)
    metar = metar.replace("\n", "")
    metar = metar.strip()

    return metar


def __get_metar_from_report_line__(metar_report_line_from_webpage):
    """
    Extracts the METAR from the line in the webpage and sets
    the data into the cache.

    Returns None if an error occurs or nothing can be found.

    Arguments:
        metar_report_line_from_webpage {string} -- The line that contains the METAR from the web report.

    Returns:
        string,string -- The identifier and extracted METAR (if any), or None
    """

    identifier = None
    metar_report = None

    try:
        metar_report = __extract_metar_from_html_line__(
            metar_report_line_from_webpage)
        metar_report = metar_report.replace("METAR ", "")
        metar_report = metar_report.replace("SPECI ", "")

        if len(metar_report) < 1:
            return (None, None)

        identifier = metar_report.split(" ")[0]
        __metar_report_cache__.set(identifier, metar_report)
    except Exception:
        metar_report = None

    return (identifier, metar_report)


def __is_station_ok_to_call__(icao_code: str) -> bool:
    """
    Tells us if a station is OK to make a call to.
    This rate limits calls when a METAR is expired
    but the station has not yet updated.

    Args:
        icao_code (str): The station identifier code.

    Returns:
        bool: True if that station is OK to call.
    """

    if icao_code not in __station_last_called__:
        return True

    try:
        delta_time = datetime.now(timezone.utc) - \
            __station_last_called__[icao_code]
        minutes_since_last_call = (delta_time.total_seconds()) / 60.0

        return minutes_since_last_call > 1.0
    except Exception:
        return True


def __get_cached_metars__(airport_icao_codes: list) -> dict:
    cached_metars: dict = {}

    for identifier in airport_icao_codes:
        result: CacheResult = __metar_report_cache__.get(identifier)

        if result.is_valid and result.value is not None:
            cached_metars[identifier] = result.value

    return cached_metars


def __get_metar_reports_from_web__(airport_icao_codes: list) -> dict:
    """
    Calls to the web an attempts to gets the METARs for the requested station list.

    Arguments:
        airport_icao_code {string[]} -- Array of stations to get METARs for.

    Returns:
        dictionary -- Returns a map of METARs keyed by the station code.
    """

    if not airport_icao_codes or len(airport_icao_codes) < 1:
        return {}

    metars = {}
    metar_list: str = ",".join(airport_icao_codes)
    request_url = 'https://aviationweather.gov/api/data/metar?ids={}&format=raw&hours=0&taf=off'.format(
        metar_list)
    stream = urllib.request.urlopen(request_url, timeout=2)

    stream_lines = stream.readlines()
    stream.close()
    for line in stream_lines:
        line_as_string = line.decode("utf-8")

        is_report: bool = line.startswith(
            b'METAR') or line.startswith(b'SPECI')

        if not is_report:
            safe_log("Skipping line as it does not start with 'METAR': {}".format(
                line_as_string))
            continue

        identifier, metar_report = __get_metar_from_report_line__(
            line_as_string)

        if identifier is None:
            continue

        # If we get a good report, go ahead and shove it into the results.
        if metar_report is not None:
            metars[identifier] = Metar(metar_report)
            __station_last_called__[identifier] = datetime.now(timezone.utc)

    return metars


if __name__ == "__main__":
    import data_sources.airports

    print("Starting self-test")

    airports_to_test = ["KW29", "KMSN", "KAWO",
                        "KOSH", "KBVS", "KDOESNTEXIST", "KVOK"]
    starting_date_time = datetime.now(timezone.utc)
    utc_offset = timezone.utcoffset(timezone.utc, datetime.now())

    metars = get_metars(airports_to_test)
    joined_metar_report = ",".join(metars)

    print(f"BATCH={joined_metar_report}")

    for identifier in airports_to_test:
        faa_csv_identifer = data_sources.airports.get_faa_csv_identifier(
            identifier)

        metar: Metar = get_metar(identifier)

        if metar is None:
            print(f"ERROR: unable to get metar for '{identifier}'")
            continue

        age = metar.get_age()
        flight_category = metar.get_category()
        print(f"{identifier}: {flight_category}: {metar}")
