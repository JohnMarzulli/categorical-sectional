"""
Handles fetching and decoding weather.
"""

# Airports data can be sourced from https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/
# using the APT link, then using APT_BASE.csv
#
# It can be more directly sourced from https://ourairports.com/countries/US/airports.csv

import csv
import os
import re
import threading
import urllib.request
from datetime import datetime, timedelta, timezone

import requests

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from configuration import configuration
from lib.colors import clamp
from lib.safe_logging import safe_log, safe_log_warning

INVALID = "INVALID"
INOP = "INOP"
VFR = "VFR"
MVFR = f"M{VFR}"
IFR = "IFR"
LIFR = f"L{IFR}"
NIGHT = "NIGHT"
NIGHT_DARK = "DARK"
SMOKE = "SMOKE"

LOW = "LOW"
OFF = "OFF"

DRIZZLE = "DRIZZLE"
RAIN = "RAIN"
HEAVY_RAIN = f"HEAVY {RAIN}"
SNOW = "SNOW"
ICE = "ICE"
UNKNOWN = "UNKNOWN"

__cache_lock__ = threading.Lock()
__rest_session__ = requests.Session()
__daylight_cache__ = {}
__metar_report_cache__ = {}
__station_last_called__ = {}

DEFAULT_READ_SECONDS = 15
DEFAULT_METAR_LIFESPAN_MINUTES = 60
DEFAULT_METAR_INVALIDATE_MINUTES = DEFAULT_METAR_LIFESPAN_MINUTES * 1.5


def __now_utc__() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)


def __load_airport_data__(
    working_directory=os.path.dirname(os.path.abspath(__file__)),
    airport_data_file="../data/us-airports.csv",
):
    """
    Loads all of the airport and weather station data from the included CSV file
    then places it into a dictionary for easy use.

    The data can be updated from https://ourairports.com/countries/US/airports.csv

    Keyword Arguments:
        airport_data_file {str} -- The file that contains the airports (default: {"../data/us-airports.csv"})

    Returns:
        dictionary -- A map of the airport data keyed by ICAO code.
    """
    full_file_path = os.path.join(
        working_directory, os.path.normpath(airport_data_file)
    )

    csv_file = open(full_file_path, "r", encoding="utf-8")

    fieldnames = (
        "id",
        "ident",
        "type",
        "name",
        "latitude_deg",
        "longitude_deg",
        "elevation_ft",
        "continent",
        "iso_country",
        "iso_region",
        "municipality",
        "scheduled_service",
        "gps_code",
        "iata_code",
        "local_code",
        "home_link",
        "wikipedia_link",
        "keywords",
    )
    reader = csv.DictReader(csv_file, fieldnames)

    airport_to_location = {}

    for row in reader:
        airport_to_location[row["ident"]] = {
            "lat": row["latitude_deg"],
            "long": row["longitude_deg"],
        }

    return airport_to_location


__airport_locations__ = __load_airport_data__()


def __get_utc_datetime__(datetime_string: str) -> datetime:
    """
    Parses the RFC format datetime into something we can use.

    Arguments:
        datetime_string {string} -- The RFC encoded datetime string.

    Returns:
        datetime -- The parsed date time.
    """

    dt = datetime.fromisoformat(datetime_string.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def __set_cache__(station_icao_code: str, cache: dict, value):
    """
    Sets the given cache to have the given value.
    Automatically sets the cache saved time.

    Arguments:
        airport_icao_code {str} -- The code of the station to cache the results for.
        cache {dictionary} -- The cache keyed by airport code.
        value {object} -- The value to store in the cache.
    """

    __cache_lock__.acquire()
    try:
        cache[station_icao_code] = datetime.now(timezone.utc), value
    finally:
        __cache_lock__.release()


def __is_cache_valid__(
    station_icao_code: str, cache: dict, cache_life_in_minutes: int = 8
):
    """
    Returns TRUE and the cached value if the cached value
    can still be used.

    Arguments:
        airport_icao_code {str} -- The airport code to get from the cache.
        cache {dictionary} -- Tuple of last update time and value keyed by airport code.
        cache_life_in_minutes {int} -- How many minutes until the cached value expires

    Returns:
        [type] -- [description]
    """

    __cache_lock__.acquire()

    if cache is None:
        return (False, None)

    now = datetime.now(timezone.utc)

    try:
        if station_icao_code in cache:
            time_since_last_fetch = now - cache[station_icao_code][0]

            if time_since_last_fetch is not None and (
                ((time_since_last_fetch.total_seconds()) / 60.0) < cache_life_in_minutes
            ):
                return (True, cache[station_icao_code][1])
            else:
                return (False, cache[station_icao_code][1])
    except Exception:
        pass
    finally:
        __cache_lock__.release()

    return (False, None)


def get_faa_csv_identifier(station_icao_code: str) -> str | None:
    """
    Checks to see if the given identifier is in the FAA CSV file.
    If it is not, then checks to see if it is one of the airports
    that the weather service requires a "K" prefix, but the CSV
    file is without it.

    Returns any identifier that is in the CSV file.
    Returns None if the airport is not in the file.

    Arguments:
        airport_icao_code {string} -- The full identifier of the airport.
    """

    if station_icao_code is None:
        return None

    normalized_icao_code = station_icao_code.upper()

    if normalized_icao_code in __airport_locations__:
        return normalized_icao_code

    if len(normalized_icao_code) >= 4:
        normalized_icao_code = normalized_icao_code[-3:]

        if normalized_icao_code in __airport_locations__:
            return normalized_icao_code

    if len(normalized_icao_code) <= 3:
        normalized_icao_code = f"K{normalized_icao_code}"

        if normalized_icao_code in __airport_locations__:
            return normalized_icao_code

    return None


def get_civil_twilight(
    station_icao_code: str,
    current_utc_time: datetime = __now_utc__(),
    use_cache: bool = True,
) -> list[datetime] | None:
    """
    Gets the civil twilight time for the given airport

    Arguments:
        airport_icao_code {string} -- The ICAO code of the airport.

    Returns:
        An array that describes the following:
        0 - When sunrise starts
        1 - when sunrise is
        2 - when full light starts
        3 - when full light ends
        4 - when sunset starts
        5 - when it is full dark
    """

    result = __is_cache_valid__(station_icao_code, __daylight_cache__, 4 * 60)
    is_cache_valid: bool = result[0]
    cached_value: list[datetime] = result[1]

    # Make sure that the sunrise time we are using is still valid...
    if is_cache_valid:
        hours_since_sunrise = (
            current_utc_time - cached_value[1]
        ).total_seconds() / 3600
        if hours_since_sunrise > 24:
            is_cache_valid = False
            safe_log_warning(
                f"Twilight cache for {station_icao_code} had a HARD miss with delta={hours_since_sunrise}"
            )
            current_utc_time += timedelta(hours=1)

    if is_cache_valid and use_cache:
        return cached_value

    faa_code = get_faa_csv_identifier(station_icao_code)

    if faa_code is None:
        return None

    # Using "formatted=0" returns the times in a full datetime format
    # Otherwise you need to do some silly math to figure out the date
    # of the sunrise or sunset.
    lat = str(__airport_locations__[faa_code]["lat"])
    lon = str(__airport_locations__[faa_code]["long"])
    year = str(current_utc_time.year)
    month = str(current_utc_time.month)
    day = str(current_utc_time.day)
    url = f"http://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={year}-{month}-{day}&formatted=0"

    json_result = []
    try:
        json_result = __rest_session__.get(url, timeout=DEFAULT_READ_SECONDS).json()
    except Exception as ex:
        safe_log_warning(f"~get_civil_twilight() => None; EX:{ex}")
        return []

    if (
        json_result is not None
        and "status" in json_result
        and json_result["status"] == "OK"
        and "results" in json_result
    ):
        sunrise = __get_utc_datetime__(json_result["results"]["sunrise"])
        sunset = __get_utc_datetime__(json_result["results"]["sunset"])
        sunrise_start = __get_utc_datetime__(
            json_result["results"]["civil_twilight_begin"]
        )
        sunset_end = __get_utc_datetime__(json_result["results"]["civil_twilight_end"])
        sunrise_length = sunrise - sunrise_start
        sunset_length = sunset_end - sunset
        avg_transition_time = timedelta(
            seconds=(sunrise_length.seconds + sunset_length.seconds) / 2
        )
        sunrise_and_sunset = [
            sunrise_start,
            sunrise,
            sunrise + avg_transition_time,
            sunset - avg_transition_time,
            sunset,
            sunset_end,
        ]
        __set_cache__(station_icao_code, __daylight_cache__, sunrise_and_sunset)

        return sunrise_and_sunset

    return None


def is_daylight(
    station_icao_code: str,
    light_times: list,
    current_utc_time: datetime = __now_utc__(),
    use_cache: bool = True,
) -> bool:
    """
    Returns TRUE if the airport is currently in daylight

    Arguments:
        airport_icao_code {string} -- The airport code to test.

    Returns:
        boolean -- True if the airport is currently in daylight.
    """

    if light_times is not None and len(light_times) == 6:
        # Deal with day old data...
        hours_since_sunrise = (current_utc_time - light_times[1]).total_seconds() / 3600

        if hours_since_sunrise < 0:
            light_times: list[datetime] = get_civil_twilight(
                station_icao_code, current_utc_time - timedelta(hours=24), use_cache
            )

        if hours_since_sunrise > 24:
            return True

        # Make sure the time between takes into account
        # The amount of time sunrise or sunset takes
        is_after_sunrise = light_times[2] < current_utc_time
        is_before_sunset = current_utc_time < light_times[3]

        return is_after_sunrise and is_before_sunset

    return True


def is_night(
    station_icao_code: str,
    light_times: list,
    current_utc_time: datetime = __now_utc__(),
    use_cache: bool = True,
) -> bool:
    """
    Returns TRUE if the airport is currently in night

    Arguments:
        airport_icao_code {string} -- The airport code to test.

    Returns:
        boolean -- True if the airport is currently in night.
    """

    if light_times is not None:
        # Deal with day old data...
        hours_since_sunrise = (current_utc_time - light_times[1]).total_seconds() / 3600

        if hours_since_sunrise < 0:
            light_times = get_civil_twilight(
                station_icao_code, current_utc_time - timedelta(hours=24), use_cache
            )

        if hours_since_sunrise > 24:
            return False

        # Make sure the time between takes into account
        # The amount of time sunrise or sunset takes
        is_before_sunrise = current_utc_time < light_times[0]
        is_after_sunset = current_utc_time > light_times[5]

        return is_before_sunrise or is_after_sunset

    return False


def get_proportion_between_times(
    start: datetime, current: datetime, end: datetime
) -> float:
    """
    Gets the "distance" (0.0 to 1.0) between the start and the end where the current time is.
    IE:
        If the CurrentTime is the same as StartTime, then the result will be 0.0
        If the CurrentTime is the same as the EndTime, then the result will be 1.0
        If the CurrentTime is halfway between StartTime and EndTime, then the result will be 0.5


    Arguments:
        start {datetime} -- The starting time.
        current {datetime} -- The time we want to get the proportion for.
        end {datetime} -- The end time to calculate the interpolaton for.

    Returns:
        float -- The amount of interpolaton for Current between Start and End
    """

    if current < start:
        return 0.0

    if current > end:
        return 1.0

    total_delta = (end - start).total_seconds()
    time_in = (current - start).total_seconds()

    return time_in / total_delta


def get_twilight_transition(airport_icao_code, current_utc_time=None, use_cache=True):
    """
    Returns the mix of dark & color fade for twilight transitions.

    Arguments:
        airport_icao_code {string} -- The ICAO code of the weather station.

    Keyword Arguments:
        current_utc_time {datetime} -- The time in UTC to calculate the mix for. (default: {None})
        use_cache {bool} -- Should the cache be used to determine the sunrise/sunset/transition data. (default: {True})

    Returns:
        tuple -- (proportion_off_to_night, proportion_night_to_category)
    """

    if current_utc_time is None:
        current_utc_time = datetime.now(timezone.utc)

    light_times = get_civil_twilight(airport_icao_code, current_utc_time, use_cache)

    if light_times is None or len(light_times) < 5:
        return 0.0, 1.0

    if is_daylight(airport_icao_code, light_times, current_utc_time, use_cache):
        return 0.0, 1.0

    if is_night(airport_icao_code, light_times, current_utc_time, use_cache):
        return 0.0, 0.0

    proportion_off_to_night = 0.0
    proportion_night_to_color = 0.0

    # Sunsetting: Night to off
    if current_utc_time >= light_times[4]:
        proportion_off_to_night = 1.0 - get_proportion_between_times(
            light_times[4], current_utc_time, light_times[5]
        )
    # Sunsetting: Color to night
    elif current_utc_time >= light_times[3]:
        proportion_night_to_color = 1.0 - get_proportion_between_times(
            light_times[3], current_utc_time, light_times[4]
        )
    # Sunrising: Night to color
    elif current_utc_time >= light_times[1]:
        proportion_night_to_color = get_proportion_between_times(
            light_times[1], current_utc_time, light_times[2]
        )
    # Sunrising: off to night
    else:
        proportion_off_to_night = get_proportion_between_times(
            light_times[0], current_utc_time, light_times[1]
        )

    proportion_off_to_night = clamp(-1.0, proportion_off_to_night, 1.0)
    proportion_night_to_color = clamp(-1.0, proportion_night_to_color, 1.0)

    return proportion_off_to_night, proportion_night_to_color


def extract_metar_from_html_line(raw_metar_line):
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


def get_metar_from_report_line(metar_report_line_from_webpage):
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
    metar = None

    try:
        metar = extract_metar_from_html_line(metar_report_line_from_webpage)
        metar = metar.replace("METAR ", "")
        metar = metar.replace("SPECI ", "")

        if len(metar) < 1:
            return (None, None)

        identifier = metar.split(" ")[0]
        __set_cache__(identifier, __metar_report_cache__, metar)
    except Exception:
        metar = None

    return (identifier, metar)


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


def get_metars(airport_icao_codes: list) -> list:
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_icao_code {string} -- The list of ICAO code for the weather station.

    Returns:
        dictionary - A dictionary (keyed by airport code) of the RAW metars.
        Returns INVALID as the value for the key if an error occurs.
    """

    metars = {}

    # For the airports and identifiers that we were not able to get
    # a result for, see if we can fill in the results.
    for identifier in airport_icao_codes:
        # If we did not get a report, but do
        # still have an old report, then use the old
        # report.
        cache_valid, report = __is_cache_valid__(identifier, __metar_report_cache__)

        is_ready_to_call = __is_station_ok_to_call__(identifier)

        if cache_valid and report is not None and not is_ready_to_call:
            # Falling back to cached METAR for rate limiting
            metars[identifier] = report
        else:
            try:
                new_metars = get_metar_reports_from_web([identifier])
                new_report = new_metars[identifier]

                safe_log(f"New WX for {identifier}={new_report}")

                if new_report is None or len(new_report) < 1:
                    continue

                __set_cache__(identifier, __metar_report_cache__, new_report)
                metars[identifier] = new_report

                safe_log(f"{identifier}:{new_report}")

            except Exception as e:
                safe_log_warning(f"get_metars, being set to INVALID EX:{e}")

                metars[identifier] = INVALID

    return metars


def get_metar_reports_from_web(airport_icao_codes: list):
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

        identifier, metar = get_metar_from_report_line(line_as_string)

        if identifier is None:
            continue

        # If we get a good report, go ahead and shove it into the results.
        if metar is not None:
            metars[identifier] = metar
            __station_last_called__[identifier] = datetime.utcnow()

    return metars


def get_metar(airport_icao_code: str, use_cache: bool = True) -> str:
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_icao_code {string} -- The ICAO code for the weather station.

    Keyword Arguments:
        use_cache {bool} -- Should we use the cache? Set to false to bypass the cache. (default: {True})
    """

    if airport_icao_code is None or not airport_icao_code:
        safe_log("Invalid or empty airport code")

    is_cache_valid, cached_metar = __is_cache_valid__(
        airport_icao_code, __metar_report_cache__
    )

    # Make sure that we used the most recent reports we can.
    # Metars are normally updated hourly.
    if is_cache_valid and cached_metar != INVALID:
        metar_age = get_metar_age(cached_metar).total_seconds() / 60.0

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


def get_station_from_metar(metar: str) -> str:
    """
    Given a METAR, extract the station identifier.

    Args:
        metar (str): The METAR to get the station name from.

    Returns:
        str: The name of the station if extracted and valid, otherwise None
    """
    if metar is None:
        return None

    if len(metar) < 3:
        return None

    try:
        tokens = metar.split(" ")

        if tokens is None or not tokens:
            return None

        station = tokens[0]

        if len(station) < 2 or len(station) > 8:
            return None

        return station
    except Exception:
        return None


def get_metar_timestamp(metar: str, current_time: datetime = __now_utc__()) -> datetime:
    try:
        metar_date = current_time - timedelta(days=31)

        if metar is not None and metar != INVALID:
            partial_date_time = metar.split(" ")[1]
            partial_date_time = partial_date_time.split("Z")[0]

            day_number = int(partial_date_time[:2])
            hour = int(partial_date_time[2:4])
            minute = int(partial_date_time[4:6])

            metar_date = datetime(
                current_time.year,
                current_time.month,
                day_number,
                hour,
                minute,
                tzinfo=timezone.utc,
            )

            # Assume that the report is from the past, and work backwards.
            days_back = 0
            while metar_date.day != day_number and days_back <= 31:
                metar_date -= timedelta(days=1)
                days_back += 1

        return metar_date
    except Exception:
        return None


def get_metar_age(metar: str, current_time: datetime = __now_utc__()) -> timedelta:
    """
    Returns the age of the METAR

    Arguments:
        metar {string} -- The METAR to get the age from.

    Returns:
        timedelta -- The age of the metar, None if it can not be determined.
    """

    try:
        metar_date = get_metar_timestamp(metar, current_time)

        return current_time - metar_date
    except Exception as e:
        safe_log_warning(f"Exception while getting METAR age:{e}")
        return None


def is_lightning(metar: str) -> bool:
    """
    Checks if the metar contains a report for lightning.

    Args:
        metar (str): The metar to see if it contains lightning.

    Returns:
        bool: True if the metar contains lightning.
    """
    return False if metar is None else re.search(".* LTG.*", metar) is not None


def get_visibility(metar):
    """
    Returns the flight rules classification based on visibility from a RAW metar.

    Arguments:
        metar {string} -- The RAW weather report in METAR format.

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """

    match = re.search("( [0-9] )?([0-9]/?[0-9]?SM)", metar)
    is_smoke = re.search(".* FU .*", metar) is not None
    # Not returning a visibility indicates UNLIMITED
    if match == None:
        return VFR
    (g1, g2) = match.groups()
    if g2 == None:
        return INVALID
    if g1 != None:
        if is_smoke:
            return SMOKE
        return IFR
    if "/" in g2:
        if is_smoke:
            return SMOKE
        return LIFR
    vis = int(re.sub("SM", "", g2))
    if vis < 3:
        if is_smoke:
            return SMOKE
        return IFR
    if vis <= 5:
        if is_smoke:
            return SMOKE

        return MVFR
    return VFR


def get_main_metar_components(metar: str) -> list | None:
    return None if metar is None else metar.split("RMK")[0].split(" ")[1:]


def get_ceiling(metar):
    """
    Returns the flight rules classification based on ceiling from a RAW metar.

    Arguments:
        metar {string} -- The RAW weather report in METAR format.

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """

    # Exclude the remarks from being parsed as the current
    # condition as they normally are for events that
    # are in the past.
    components = get_main_metar_components(metar)
    minimum_ceiling = 10000
    for component in components:
        if "BKN" in component or "OVC" in component:
            try:
                ceiling = int("".join(filter(str.isdigit, component))) * 100

                if ceiling < minimum_ceiling:
                    minimum_ceiling = ceiling
            except Exception as ex:
                safe_log_warning(
                    f"Unable to decode ceiling component {component} from {metar}. EX:{ex}"
                )
    return minimum_ceiling


def get_temperature(metar: str) -> int | None:
    """
    Returns the temperature (celsius) from the given metar string.

    Args:
        metar (string): The metar to extract the temperature reading from.

    Returns:
        int: The temperature in celsius.
    """
    if metar is None:
        return None

    components = get_main_metar_components(metar)

    for component in components:
        if (
            "/" in component
            and "SM" not in component
            and "R" not in component
            and "P" not in component
            and "U" not in component
        ):
            raw_temperature = component.split("/")[0]
            is_below_zero = "M" in raw_temperature
            temp = int(raw_temperature.replace("M", "", 0))

            if is_below_zero:
                temp = 0 - temp

            return temp

    return None


def get_pressure(metar: str) -> float | None:
    """
    Get the inches of mercury from a METAR.
    This **DOES NOT** extract the Sea Level Pressure
    from the remarks section.

    Args:
        metar (str): The metar to extract the pressure from.

    Returns:
        float: None if not found, otherwise the inches of mercury. EX:29.92
    """
    components = get_main_metar_components(metar)

    try:
        for component in components:
            is_altimeter = re.search("A\d{4}", component) is not None

            if is_altimeter:
                inches_of_mercury = float(component.split("A")[1]) / 100.0

                return inches_of_mercury
    except Exception:
        pass

    return None


def get_precipitation(metar: str) -> str | None:
    if metar is None:
        return None

    components = get_main_metar_components(metar)

    for component in components:
        if "UP" in component:
            return UNKNOWN
        elif "RA" in component:
            return HEAVY_RAIN if "+" in component else RAIN
        elif (
            "GR" in component
            or "GS" in component
            or "IC" in component
            or "PL" in component
        ):
            return ICE
        elif "SN" in component or "SG" in component:
            return SNOW
        elif "DZ" in component:
            return DRIZZLE

    return None


def get_ceiling_category(ceiling) -> str:
    """
    Returns the flight rules classification based on the cloud ceiling.

    Arguments:
        ceiling {int} -- Number of feet the clouds are above the ground.

    Returns:
        string -- The flight rules classification.
    """

    if ceiling <= 500:
        return LIFR
    if ceiling <= 1000:
        return IFR
    if ceiling <= 3000:
        return MVFR
    return VFR


def is_station_inoperative(metar: str) -> bool:
    """
    Tells you if the weather station is operative or inoperative.
    Inoperative is mostly defined as not having an updated METAR
    in the allowable time period.

    Args:
        metar (str): The METAR to check.

    Returns:
        bool: True if the station is INOPERATIVE. This means the METAR should be ignored.
    """
    if metar is None or metar == INVALID:
        return True

    metar_age = get_metar_age(metar)

    if metar_age is not None:
        metar_age_minutes = metar_age.total_seconds() / 60.0
        metar_inactive_threshold = configuration.get_metar_station_inactive_minutes()

        return metar_age_minutes > metar_inactive_threshold

    return False


def get_category(airport_icao_code: str, metar: str) -> str:
    """
    Returns the flight rules classification based on the entire RAW metar.

    Arguments:
        airport_icao_code -- The airport or weather station that we want to get a category for.
        metar {string} -- The RAW weather report in METAR format.
        return_night {boolean} -- Should we return a category for NIGHT?

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """
    if metar is None or metar == INVALID:
        return INVALID

    if airport_icao_code is None:
        return INVALID

    if len(metar) < 4:
        return INVALID

    vis = get_visibility(metar)
    ceiling = get_ceiling_category(get_ceiling(metar))
    if ceiling == INVALID or vis == INVALID:
        return INVALID
    if vis == SMOKE:
        return SMOKE
    if vis == LIFR or ceiling == LIFR:
        return LIFR
    if vis == IFR or ceiling == IFR:
        return IFR
    if vis == MVFR or ceiling == MVFR:
        return MVFR

    return VFR


if __name__ == "__main__":
    print("Starting self-test")

    airports_to_test = ["KW29", "KMSN", "KAWO", "KOSH", "KBVS", "KDOESNTEXIST"]
    starting_date_time = datetime.now(timezone.utc)
    utc_offset = timezone.utcoffset(timezone.utc, datetime.now())

    get_category(
        "KVOK",
        "KVOK 251453Z 34004KT 10SM SCT008 OVC019 21/21 A2988 RMK AO2A SCT V BKN SLP119 53012",
    )

    metars = get_metars(airports_to_test)
    kawo_metar = get_metar("KAWO", use_cache=False)
    joined_metar_report = ",".join(metars)

    print(f"BATCH={joined_metar_report}")
    print(f"KAWO={kawo_metar}")

    light_times = get_civil_twilight("KAWO", starting_date_time)

    print("Sunrise start:{0}".format(light_times[0] - utc_offset))
    print("Sunrise:{0}".format(light_times[1] - utc_offset))
    print("Full light:{0}".format(light_times[2] - utc_offset))
    print("Sunset start:{0}".format(light_times[3] - utc_offset))
    print("Sunset:{0}".format(light_times[4] - utc_offset))
    print("Full dark:{0}".format(light_times[5] - utc_offset))

    for identifier in airports_to_test:
        faa_csv_identifer = get_faa_csv_identifier(identifier)

        metar = get_metar(identifier)
        age = get_metar_age(metar)
        flight_category = get_category(identifier, metar)
        print(f"{identifier}: {flight_category}: {metar}")

    for hours_ahead in range(0, 240):
        hours_ahead *= 0.1
        time_to_fetch = starting_date_time + timedelta(hours=hours_ahead)
        local_fetch_time = time_to_fetch - utc_offset

        for airport in ["KW29", "KAWO"]:  # , 'KCOE', 'KMSP', 'KOSH']:
            light_times = get_civil_twilight(airport, time_to_fetch)
            is_lit = is_daylight(airport, light_times, time_to_fetch)
            is_dark = is_night(airport, light_times, time_to_fetch)
            transition = get_twilight_transition(airport, time_to_fetch)

            print(
                "DELTA=+{0:.1f}, LOCAL={1}, AIRPORT={2}: is_day={3}, is_night={4}, p_dark:{5:.1f}, p_color:{6:.1f}".format(
                    hours_ahead,
                    local_fetch_time,
                    airport,
                    is_lit,
                    is_dark,
                    transition[0],
                    transition[1],
                )
            )
