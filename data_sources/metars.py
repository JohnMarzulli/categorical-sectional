import contextlib
import os
import re
from datetime import datetime, timedelta, timezone

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from configuration import configuration
from lib.safe_logging import safe_log_warning
import data_sources.time

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


def get_station_from_metar(metar: str) -> str | None:
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

        return None if len(station) < 2 or len(station) > 8 else station
    except Exception:
        return None


def get_metar_timestamp(
    metar: str, current_time: datetime = data_sources.time.now_utc()
) -> datetime:
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
        return datetime.now(timezone.utc) - timedelta(days=30)


def get_metar_age(
    metar: str | None, current_time: datetime = data_sources.time.now_utc()
) -> timedelta:
    """
    Returns the age of the METAR

    Arguments:
        metar {string} -- The METAR to get the age from.

    Returns:
        timedelta -- The age of the metar, None if it can not be determined.
    """

    if metar is None:
        return timedelta(days=30)

    try:
        metar_date = get_metar_timestamp(metar, current_time)

        return current_time - metar_date
    except Exception as e:
        safe_log_warning(f"Exception while getting METAR age:{e}")
        return timedelta(days=30)


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

    >>> get_visibility('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'VFR'
    >>> get_visibility('KRNT 132053Z 33010KT 4SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'MVFR'
    >>> get_visibility('KRNT 132053Z 33010KT 3SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'MVFR'
    >>> get_visibility('KRNT 132053Z 33010KT 2 1/2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'IFR'
    >>> get_visibility('KRNT 132053Z 33010KT 2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'IFR'
    >>> get_visibility('KRNT 132053Z 33010KT 1SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'IFR'
    >>> get_visibility('KRNT 132053Z 33010KT 1/2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'LIFR'
    >>> get_visibility('KGCC 231853Z AUTO 28011KT 20/12 A2991 RMK AO2 LTG DSNT SE RAB41RAEMM SLP085 P0000 T02000117 PWINO $')
    'VFR'
    >>> get_visibility('KVOK 251453Z 34004KT 10SM SCT008 OVC019 21/21 A2988 RMK AO2A SCT V BKN SLP119 53012')
    'VFR'
    """

    match = re.search("( [0-9] )?([0-9]/?[0-9]?SM)", metar)
    is_smoke = re.search(".* FU .*", metar) is not None
    # Not returning a visibility indicates UNLIMITED
    if match is None:
        return VFR
    (g1, g2) = match.groups()
    if g2 is None:
        return INVALID
    if g1 is not None:
        return SMOKE if is_smoke else IFR
    if "/" in g2:
        return SMOKE if is_smoke else LIFR
    vis = int(re.sub("SM", "", g2))
    if vis < 3:
        return SMOKE if is_smoke else IFR
    if vis <= 5:
        return SMOKE if is_smoke else MVFR
    return VFR


def get_main_metar_components(metar: str) -> list[str]:
    return [] if metar is None else metar.split("RMK")[0].split(" ")[1:]


def get_ceiling(metar):
    """
    Returns the flight rules classification based on ceiling from a RAW metar.

    Arguments:
        metar {string} -- The RAW weather report in METAR format.

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.

    >>> get_ceiling('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    10000
    >>> get_ceiling('KRNT 132053Z 33010KT 4SM BKN041 SCT030 23/14 A3001 RMK AO2 SLP165')
    4100
    >>> get_ceiling('KRNT 132053Z 33010KT 4SM BKN041 OVC030 23/14 A3001 RMK AO2 SLP165')
    3000
    >>> get_ceiling('KRNT 132053Z 33010KT 4SM SCT041 OVC030 23/14 A3001 RMK AO2 SLP165')
    3000
    >>> get_ceiling('KRNT 132053Z 33010KT 3SM SCT041 BKN025 23/14 A3001 RMK AO2 SLP165')
    2500
    >>> get_ceiling('KRNT 132053Z 33010KT 2 1/2SM SCT041 BKN009 23/14 A3001 RMK AO2 SLP165')
    900
    >>> get_ceiling('KRNT 132053Z 33010KT 2 1/2SM SCT041 OVC009 23/14 A3001 RMK AO2 SLP165')
    900
    >>> get_ceiling('KRNT 132053Z 33010KT 2SM OVC004 23/14 A3001 RMK AO2 SLP165')
    400
    >>> get_ceiling('KRNT 132053Z 33010KT 2SM SCT010 OVC004 23/14 A3001 RMK AO2 SLP165')
    400
    >>> get_ceiling('KGCC 231853Z AUTO 28011KT 20/12 A2991 RMK AO2 LTG DSNT SE RAB41RAEMM SLP085 P0000 T02000117 PWINO $')
    10000
    >>> get_ceiling('KVOK 251453Z 34004KT 10SM SCT008 OVC019 21/21 A2988 RMK AO2A SCT V BKN SLP119 53012')
    1900
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


def get_temperature(metar: str):
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

    with contextlib.suppress(Exception):
        for component in components:
            is_altimeter = re.search("A\\d{4}", component) is not None

            if is_altimeter:
                return float(component.split("A")[1]) / 100.0
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

    >>> get_ceiling_category(get_ceiling('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165'))
    'VFR'
    >>> get_ceiling_category(get_ceiling('KRNT 132053Z 33010KT 4SM SCT041 OVC030 23/14 A3001 RMK AO2 SLP165'))
    'MVFR'
    >>> get_ceiling_category(get_ceiling('KRNT 132053Z 33010KT 3SM SCT041 BKN025 23/14 A3001 RMK AO2 SLP165'))
    'MVFR'
    >>> get_ceiling_category(get_ceiling('KRNT 132053Z 33010KT 2 1/2SM SCT041 BKN009 23/14 A3001 RMK AO2 SLP165'))
    'IFR'
    >>> get_ceiling_category(get_ceiling('KRNT 132053Z 33010KT 2 1/2SM SCT041 OVC009 23/14 A3001 RMK AO2 SLP165'))
    'IFR'
    >>> get_ceiling_category(get_ceiling('KRNT 132053Z 33010KT 2SM OVC004 23/14 A3001 RMK AO2 SLP165'))
    'LIFR'
    >>> get_ceiling_category(get_ceiling('KRNT 132053Z 33010KT 2SM SCT010 OVC004 23/14 A3001 RMK AO2 SLP165'))
    'LIFR'
    >>> get_ceiling_category(get_ceiling('KGCC 231853Z AUTO 28011KT 20/12 A2991 RMK AO2 LTG DSNT SE RAB41RAEMM SLP085 P0000 T02000117 PWINO $'))
    'VFR'
    >>> get_ceiling_category(get_ceiling('KVOK 251453Z 34004KT 10SM SCT008 OVC019 21/21 A2988 RMK AO2A SCT V BKN SLP119 53012'))
    'MVFR'
    """

    if ceiling <= 500:
        return LIFR
    if ceiling <= 1000:
        return IFR
    return MVFR if ceiling <= 3000 else VFR


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


def get_category(airport_icao_code: str, metar: str | None) -> str:
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
    return MVFR if vis == MVFR or ceiling == MVFR else VFR


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
