from datetime import datetime, timedelta, timezone

import requests

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import data_sources.airports
import lib.time
from lib.cache import Cache, CacheResult
from lib.interpolation import clamp
from lib.safe_logging import safe_log_warning
from meteorology.types.daylight_hours import DaylightHours

__daylight_cache__: Cache = Cache(4 * 60)
__rest_session__ = requests.Session()
DEFAULT_READ_SECONDS = 15


def __get_datetime_hour__(hour: float) -> datetime:
    now = lib.time.now_utc()
    # Set today's time to the specified hour (supports fractional hours)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    now = start_of_day + timedelta(hours=hour)

    return now


def __get_civil_twilight_from_source__(
    station_code: str,
    current_utc_time: datetime = lib.time.now_utc(),
) -> DaylightHours:
    # Using "formatted=0" returns the times in a full datetime format
    # Otherwise you need to do some silly math to figure out the date
    # of the sunrise or sunset.
    location = data_sources.airports.get_location(station_code)

    year = str(current_utc_time.year)
    month = str(current_utc_time.month)
    day = str(current_utc_time.day)
    url = f"http://api.sunrise-sunset.org/json?lat={location.lat}&lng={location.lon}&date={year}-{month}-{day}&formatted=0"

    json_result = []

    default_response = DaylightHours(
        __get_datetime_hour__(4),
        __get_datetime_hour__(6),
        __get_datetime_hour__(8),
        __get_datetime_hour__(16),
        __get_datetime_hour__(18),
        __get_datetime_hour__(20),
    )

    try:
        json_result = __rest_session__.get(url, timeout=DEFAULT_READ_SECONDS).json()
    except Exception as ex:
        safe_log_warning(f"~get_civil_twilight() => None; EX:{ex}")
        return default_response

    if (
        json_result is not None
        and "status" in json_result
        and json_result["status"] == "OK"
        and "results" in json_result
    ):
        sunrise = lib.time.get_utc_datetime(json_result["results"]["sunrise"])
        sunset = lib.time.get_utc_datetime(json_result["results"]["sunset"])
        sunrise_start = lib.time.get_utc_datetime(
            json_result["results"]["civil_twilight_begin"]
        )
        sunset_end = lib.time.get_utc_datetime(
            json_result["results"]["civil_twilight_end"]
        )
        sunrise_length = sunrise - sunrise_start
        sunset_length = sunset_end - sunset
        avg_transition_time = timedelta(
            seconds=(sunrise_length.seconds + sunset_length.seconds) / 2
        )
        return DaylightHours(
            sunrise_start,
            sunrise,
            sunrise + avg_transition_time,
            sunset - avg_transition_time,
            sunset,
            sunset_end,
        )

    return default_response


def get_civil_twilight(
    station_icao_code: str,
    current_utc_time: datetime = lib.time.now_utc(),
) -> DaylightHours:
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

    result: CacheResult = __daylight_cache__.get_or_set(
        station_icao_code,
        lambda: __get_civil_twilight_from_source__(station_icao_code, current_utc_time),
    )
    cached_value: DaylightHours = result.value  # type: ignore

    if result.is_valid:
        hours_since_sunrise = (
            current_utc_time - cached_value.sunrise
        ).total_seconds() / 3600

        if hours_since_sunrise > 24:
            safe_log_warning(
                f"Twilight cache for {station_icao_code} had a HARD miss with delta={hours_since_sunrise}"
            )
            current_utc_time += timedelta(hours=1)

    return cached_value


def is_daylight(
    station_icao_code: str,
    light_times: DaylightHours,
    current_utc_time: datetime = lib.time.now_utc(),
) -> bool:
    """
    Returns TRUE if the airport is currently in daylight

    Arguments:
        airport_icao_code {string} -- The airport code to test.

    Returns:
        boolean -- True if the airport is currently in daylight.
    """

    # Deal with day old data...
    hours_since_sunrise = (
        current_utc_time - light_times.sunrise_start
    ).total_seconds() / 3600

    if hours_since_sunrise < 0:
        light_times = get_civil_twilight(
            station_icao_code, current_utc_time - timedelta(hours=24)
        )

    if hours_since_sunrise > 24:
        return True

    # Make sure the time between takes into account
    # The amount of time sunrise or sunset takes
    is_after_sunrise = light_times.sunrise < current_utc_time
    is_before_sunset = current_utc_time < light_times.sunset

    return is_after_sunrise and is_before_sunset


def is_night(
    station_icao_code: str,
    light_times: DaylightHours,
    current_utc_time: datetime = lib.time.now_utc(),
) -> bool:
    """
    Returns TRUE if the airport is currently in night

    Arguments:
        airport_icao_code {string} -- The airport code to test.

    Returns:
        boolean -- True if the airport is currently in night.
    """

    # Deal with day old data...
    hours_since_sunrise = (
        current_utc_time - light_times.sunrise
    ).total_seconds() / 3600

    if hours_since_sunrise < 0:
        light_times = get_civil_twilight(
            station_icao_code, current_utc_time - timedelta(hours=24)
        )

    if hours_since_sunrise > 24:
        return False

    # Make sure the time between takes into account
    # The amount of time sunrise or sunset takes
    is_before_sunrise = current_utc_time < light_times.sunrise_start
    is_after_sunset = current_utc_time > light_times.sunset_end

    return is_before_sunrise or is_after_sunset


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


def get_twilight_transition(airport_icao_code, current_utc_time=None) -> list:
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

    light_times = get_civil_twilight(airport_icao_code, current_utc_time)

    if is_daylight(airport_icao_code, light_times, current_utc_time):
        return [0.0, 1.0]

    if is_night(airport_icao_code, light_times, current_utc_time):
        return [0.0, 0.0]

    proportion_off_to_night = 0.0
    proportion_night_to_color = 0.0

    # Sunsetting: Night to off
    if current_utc_time >= light_times.sunset:
        proportion_off_to_night = 1.0 - get_proportion_between_times(
            light_times.sunset, current_utc_time, light_times.sunset_end
        )
    # Sunsetting: Color to night
    elif current_utc_time >= light_times.full_light_end:
        proportion_night_to_color = 1.0 - get_proportion_between_times(
            light_times.full_light_end, current_utc_time, light_times.sunset
        )
    # Sunrising: Night to color
    elif current_utc_time >= light_times.sunrise:
        proportion_night_to_color = get_proportion_between_times(
            light_times.sunrise, current_utc_time, light_times.full_light_start
        )
    # Sunrising: off to night
    else:
        proportion_off_to_night = get_proportion_between_times(
            light_times.sunrise_start, current_utc_time, light_times.sunrise
        )

    proportion_off_to_night = clamp(-1.0, proportion_off_to_night, 1.0)
    proportion_night_to_color = clamp(-1.0, proportion_night_to_color, 1.0)

    return [proportion_off_to_night, proportion_night_to_color]


if __name__ == "__main__":
    print("Starting self-test")

    airports_to_test = ["KW29", "KMSN", "KAWO", "KOSH", "KBVS", "KDOESNTEXIST"]
    starting_date_time = datetime.now(timezone.utc)
    utc_offset = timezone.utcoffset(timezone.utc, datetime.now())

    light_times: DaylightHours = get_civil_twilight("KAWO", starting_date_time)

    print("Sunrise start:{0}".format(light_times.sunrise_start - utc_offset))
    print("Sunrise:{0}".format(light_times.sunrise - utc_offset))
    print("Full light:{0}".format(light_times.full_light_start - utc_offset))
    print("Sunset start:{0}".format(light_times.full_light_end - utc_offset))
    print("Sunset:{0}".format(light_times.sunset - utc_offset))
    print("Full dark:{0}".format(light_times.sunset_end - utc_offset))

    for hours_ahead in range(240):
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
