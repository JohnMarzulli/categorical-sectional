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
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.cache import Cache, CacheResult
from lib.safe_logging import safe_log, safe_log_warning
from meteorology.types.metar import Metar

__rest_session__ = requests.Session()
__metar_report_cache__: Cache = Cache()
__station_last_called__ = {}

DEFAULT_READ_SECONDS = 15
DEFAULT_METAR_LIFESPAN_MINUTES = 60
DEFAULT_METAR_INVALIDATE_MINUTES = DEFAULT_METAR_LIFESPAN_MINUTES * 1.5


def get_metar(airport_icao_code: str, use_cache: bool = True) -> Metar | None:
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_icao_code {string} -- The ICAO code for the weather station.

    Keyword Arguments:
        use_cache {bool} -- Should we use the cache? Set to false to bypass the cache. (default: {True})
    """

    if airport_icao_code is None or not airport_icao_code:
        safe_log("Invalid or empty airport code")

    result: CacheResult = __metar_report_cache__.get(airport_icao_code)
    is_cache_valid: bool = result.is_valid
    cached_metar: Metar = result.value  # type: ignore

    # Make sure that we used the most recent reports we can.
    # Metars are normally updated hourly.
    if is_cache_valid and cached_metar is not None:
        metar_age = cached_metar.get_age().total_seconds() / 60.0

        if use_cache and metar_age < DEFAULT_METAR_LIFESPAN_MINUTES:
            return cached_metar

    try:
        metars = get_metars([airport_icao_code])

        if metars is None:
            safe_log(
                f"Get a None while attempting to get METAR for {airport_icao_code}"
            )

            return None

        if airport_icao_code not in metars:
            safe_log(
                f"Got a result, but {airport_icao_code} was not in results package"
            )

            return None

        return metars[airport_icao_code]

    except Exception as e:
        safe_log(f"get_metar got EX:{e}")
        safe_log("")

        return None


def get_metars(airport_icao_codes: list[str]) -> dict[str, Metar]:
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_icao_code {string} -- The list of ICAO code for the weather station.

    Returns:
        dictionary - A dictionary (keyed by airport code) of the RAW metars.
        Returns INVALID as the value for the key if an error occurs.
    """

    metars: dict[str, Metar] = {}

    # For the airports and identifiers that we were not able to get
    # a result for, see if we can fill in the results.
    for identifier in airport_icao_codes:
        # If we did not get a report, but do
        # still have an old report, then use the old
        # report.
        result: CacheResult = __metar_report_cache__.get(identifier)
        cache_valid: bool = result.is_valid
        report = result.value

        is_ready_to_call = __is_station_ok_to_call__(identifier)

        if cache_valid and report is not None and not is_ready_to_call:
            # Falling back to cached METAR for rate limiting
            metars[identifier] = report
        else:
            try:
                new_metars = __get_metar_reports_from_web__([identifier])
                new_report = new_metars[identifier]

                safe_log(f"New WX for {identifier}={new_report.metar}")

                if not new_report.is_valid():
                    continue

                __metar_report_cache__.set(identifier, new_report)
                metars[identifier] = new_report

                safe_log(f"{identifier}:{new_report}")

            except Exception as e:
                safe_log_warning(f"get_metars, being set to INVALID EX:{e}")

                if identifier in metars:
                    metars.pop(identifier)

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
        metar_report = __extract_metar_from_html_line__(metar_report_line_from_webpage)
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
        delta_time = datetime.now(timezone.utc) - __station_last_called__[icao_code]
        time_since_last_call = (delta_time.total_seconds()) / 60.0

        return time_since_last_call > 1.0
    except Exception:
        return True


def __get_metar_reports_from_web__(airport_icao_codes: list) -> dict[str, Metar]:
    """
    Calls to the web an attempts to gets the METARs for the requested station list.

    Arguments:
        airport_icao_code {string[]} -- Array of stations to get METARs for.

    Returns:
        dictionary -- Returns a map of METARs keyed by the station code.
    """

    metars = {}
    metar_list: str = "%,".join(airport_icao_codes)
    request_url = f"https://aviationweather.gov/api/data/metar?ids={metar_list}&hours=0&order=id%2C-obs&sep=true"
    stream = urllib.request.urlopen(request_url, timeout=2)

    stream_lines = stream.readlines()
    stream.close()
    for line in stream_lines:
        line_as_string = line.decode("utf-8")

        identifier, metar_report = __get_metar_from_report_line__(line_as_string)

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

    airports_to_test = ["KW29", "KMSN", "KAWO", "KOSH", "KBVS", "KDOESNTEXIST", "KVOK"]
    starting_date_time = datetime.now(timezone.utc)
    utc_offset = timezone.utcoffset(timezone.utc, datetime.now())

    metars = get_metars(airports_to_test)
    joined_metar_report = ",".join(metars)

    print(f"BATCH={joined_metar_report}")

    for identifier in airports_to_test:
        faa_csv_identifer = data_sources.airports.get_faa_csv_identifier(identifier)

        metar: Metar | None = get_metar(identifier)

        if metar is None:
            print(f"ERROR: unable to get metar for '{identifier}'")
            continue

        age = metar.get_age()
        flight_category = metar.get_category()
        print(f"{identifier}: {flight_category}: {metar}")
