import contextlib
import os
import re
from datetime import datetime, timedelta, timezone

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import meteorology.types.classifications
from lib.safe_logging import safe_log_warning
import lib.time


LOW = "LOW"
OFF = "OFF"


class Metar:
    def __init__(self, metar: str):
        self.metar: str = (
            metar.strip() if metar else meteorology.types.classifications.INVALID
        )

    def __str__(self) -> str:
        return self.metar

    def is_valid(self) -> bool:
        return (
            (self.metar is not None)
            and self.metar != meteorology.types.classifications.INVALID
            and (len(self.metar) > 4)
            and self.get_station() is not None
        )

    def get_station(self) -> str:
        """
        Given a METAR, extract the station identifier.

        Args:
            metar (str): The METAR to get the station name from.

        Returns:
            str: The name of the station if extracted and valid, otherwise None
        """
        if self.metar is None:
            return ""

        if len(self.metar) < 3:
            return ""

        try:
            tokens = self.metar.split(" ")

            if tokens is None or not tokens:
                return ""

            station = tokens[0]

            return "" if len(station) < 2 or len(station) > 8 else station
        except Exception:
            return ""

    def get_timestamp(self, current_time: datetime = lib.time.now_utc()) -> datetime:
        try:
            if (
                self.metar is not None
                and self.metar != meteorology.types.classifications.INVALID
            ):
                partial_date_time = self.metar.split(" ")[1]
                partial_date_time = partial_date_time.split("Z")[0]

                day_number = int(partial_date_time[:2])
                hour = int(partial_date_time[2:4])
                minute = int(partial_date_time[4:6])

                # Walk backwards a day at a time from "now" until we find a
                # month/year where day_number is valid, then build the final
                # datetime from THAT candidate's year/month. Building the
                # datetime up front from (current_time.year,
                # current_time.month, day_number, ...) raises ValueError
                # whenever day_number belongs to the previous month (e.g. it
                # is the 1st of the month but the latest METAR is still
                # dated the 31st of the prior month, which has no 31st in
                # the new month) -- and that exception used to skip the
                # backward-correction loop entirely, falling through to the
                # "30 days old" fallback below and marking every station
                # inactive at every month rollover.
                candidate = current_time
                days_back = 0
                while days_back <= 31:
                    if candidate.day == day_number:
                        return datetime(
                            candidate.year,
                            candidate.month,
                            day_number,
                            hour,
                            minute,
                            tzinfo=timezone.utc,
                        )
                    candidate -= timedelta(days=1)
                    days_back += 1

            return current_time - timedelta(days=31)
        except Exception:
            return datetime.now(timezone.utc) - timedelta(days=30)

    def get_age(self, current_time: datetime = lib.time.now_utc()) -> timedelta:
        """
        Returns the age of the METAR

        Arguments:
            metar {string} -- The METAR to get the age from.

        Returns:
            timedelta -- The age of the metar, None if it can not be determined.
        """

        if self.metar is None:
            return timedelta(days=30)

        try:
            metar_date = self.get_timestamp(current_time)

            return current_time - metar_date
        except Exception as e:
            safe_log_warning(f"Exception while getting METAR age:{e}")
            return timedelta(days=30)

    def has_lightning(self) -> bool:
        """
        Checks if the metar contains a report for lightning.

        Args:
            metar (str): The metar to see if it contains lightning.

        Returns:
            bool: True if the metar contains lightning.
        """
        return (
            False
            if self.metar is None
            else re.search(".* LTG.*", self.metar) is not None
        )

    def get_visibility_category(self) -> str:
        """
        Returns the flight rules classification based on visibility from a RAW metar.

        Arguments:
            metar {string} -- The RAW weather report in METAR format.

        Returns:
            string -- The flight rules classification, or INVALID in case of an error.
        """

        match = re.search("( [0-9] )?([0-9]/?[0-9]?SM)", self.metar)
        is_smoke = re.search(".* FU .*", self.metar) is not None
        # Not returning a visibility indicates UNLIMITED
        if match is None:
            return meteorology.types.classifications.VFR
        (g1, g2) = match.groups()
        if g2 is None:
            return meteorology.types.classifications.INVALID
        if g1 is not None:
            return (
                meteorology.types.classifications.SMOKE
                if is_smoke
                else meteorology.types.classifications.IFR
            )
        if "/" in g2:
            return (
                meteorology.types.classifications.SMOKE
                if is_smoke
                else meteorology.types.classifications.LIFR
            )
        vis = int(re.sub("SM", "", g2))
        if vis < 3:
            return (
                meteorology.types.classifications.SMOKE
                if is_smoke
                else meteorology.types.classifications.IFR
            )
        if vis <= 5:
            return (
                meteorology.types.classifications.SMOKE
                if is_smoke
                else meteorology.types.classifications.MVFR
            )
        return meteorology.types.classifications.VFR

    def get_main_metar_components(self) -> list:
        return [] if self.metar is None else self.metar.split("RMK")[0].split(" ")[1:]

    def get_ceiling(self) -> int:
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
        components = self.get_main_metar_components()
        minimum_ceiling = 10000
        for component in components:
            if "BKN" in component or "OVC" in component:
                try:
                    ceiling = int("".join(filter(str.isdigit, component))) * 100

                    if ceiling < minimum_ceiling:
                        minimum_ceiling = ceiling
                except Exception as ex:
                    safe_log_warning(
                        f"Unable to decode ceiling component {component} from {self.metar}. EX:{ex}"
                    )
        return minimum_ceiling

    def get_temperature(self) -> int:
        """
        Returns the temperature (celsius) from the given metar string.

        Args:
            metar (string): The metar to extract the temperature reading from.

        Returns:
            int: The temperature in celsius.
        """
        components = self.get_main_metar_components()

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

        return 0

    def get_pressure(self) -> float:
        """
        Get the inches of mercury from a METAR.
        This **DOES NOT** extract the Sea Level Pressure
        from the remarks section.

        Args:
            metar (str): The metar to extract the pressure from.

        Returns:
            float: None if not found, otherwise the inches of mercury. EX:29.92
        """
        components = self.get_main_metar_components()

        with contextlib.suppress(Exception):
            for component in components:
                is_altimeter = re.search("A\\d{4}", component) is not None

                if is_altimeter:
                    return float(component.split("A")[1]) / 100.0
        return 0.0

    def get_precipitation(self) -> str:
        components = self.get_main_metar_components()

        for component in components:
            if "UP" in component:
                return meteorology.types.classifications.UNKNOWN
            elif "RA" in component:
                return (
                    meteorology.types.classifications.HEAVY_RAIN
                    if "+" in component
                    else meteorology.types.classifications.RAIN
                )
            elif (
                "GR" in component
                or "GS" in component
                or "IC" in component
                or "PL" in component
            ):
                return meteorology.types.classifications.ICE
            elif "SN" in component or "SG" in component:
                return meteorology.types.classifications.SNOW
            elif "DZ" in component:
                return meteorology.types.classifications.DRIZZLE

        return ""

    def get_ceiling_category(self) -> str:
        """
        Returns the flight rules classification based on the cloud ceiling.

        Arguments:
            ceiling {int} -- Number of feet the clouds are above the ground.

        Returns:
            string -- The flight rules classification.
        """

        ceiling: int = self.get_ceiling()

        if ceiling <= 500:
            return meteorology.types.classifications.LIFR
        if ceiling <= 1000:
            return meteorology.types.classifications.IFR
        return (
            meteorology.types.classifications.MVFR
            if ceiling <= 3000
            else meteorology.types.classifications.VFR
        )

    def is_station_inoperative(self, metar_inactive_threshold: int = 60) -> bool:
        """
        Tells you if the weather station is operative or inoperative.
        Inoperative is mostly defined as not having an updated METAR
        in the allowable time period.

        Args:
            metar (str): The METAR to check.

        Returns:
            bool: True if the station is INOPERATIVE. This means the METAR should be ignored.
        """
        if (
            self.metar is None
            or self.metar == meteorology.types.classifications.INVALID
        ):
            return True

        metar_age = self.get_age()

        if metar_age is not None:
            metar_age_minutes = metar_age.total_seconds() / 60.0

            return metar_age_minutes > metar_inactive_threshold

        return False

    def get_category(self) -> str:
        """
        Returns the flight rules classification based on the entire RAW metar.

        Arguments:
            airport_icao_code -- The airport or weather station that we want to get a category for.
            metar {string} -- The RAW weather report in METAR format.
            return_night {boolean} -- Should we return a category for NIGHT?

        Returns:
            string -- The flight rules classification, or INVALID in case of an error.
        """

        if self.metar is None:
            return meteorology.types.classifications.INVALID

        if len(self.metar) < 4:
            return meteorology.types.classifications.INVALID

        if self.metar == meteorology.types.classifications.INVALID:
            return meteorology.types.classifications.INVALID

        vis: str = self.get_visibility_category()
        ceiling: str = self.get_ceiling_category()

        if (
            ceiling == meteorology.types.classifications.INVALID
            or vis == meteorology.types.classifications.INVALID
        ):
            return meteorology.types.classifications.INVALID
        if vis == meteorology.types.classifications.SMOKE:
            return meteorology.types.classifications.SMOKE
        if (
            vis == meteorology.types.classifications.LIFR
            or ceiling == meteorology.types.classifications.LIFR
        ):
            return meteorology.types.classifications.LIFR
        if (
            vis == meteorology.types.classifications.IFR
            or ceiling == meteorology.types.classifications.IFR
        ):
            return meteorology.types.classifications.IFR
        return (
            meteorology.types.classifications.MVFR
            if vis == meteorology.types.classifications.MVFR
            or ceiling == meteorology.types.classifications.MVFR
            else meteorology.types.classifications.VFR
        )


def test_visibility_categorization(metar_report: str) -> str:
    """
    >>> test_visibility_categorization('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'VFR'
    >>> test_visibility_categorization('KRNT 132053Z 33010KT 4SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'MVFR'
    >>> test_visibility_categorization('KRNT 132053Z 33010KT 3SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'MVFR'
    >>> test_visibility_categorization('KRNT 132053Z 33010KT 2 1/2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'IFR'
    >>> test_visibility_categorization('KRNT 132053Z 33010KT 2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'IFR'
    >>> test_visibility_categorization('KRNT 132053Z 33010KT 1SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'IFR'
    >>> test_visibility_categorization('KRNT 132053Z 33010KT 1/2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'LIFR'
    >>> test_visibility_categorization('KGCC 231853Z AUTO 28011KT 20/12 A2991 RMK AO2 LTG DSNT SE RAB41RAEMM SLP085 P0000 T02000117 PWINO $')
    'VFR'
    >>> test_visibility_categorization('KVOK 251453Z 34004KT 10SM SCT008 OVC019 21/21 A2988 RMK AO2A SCT V BKN SLP119 53012')
    'VFR'
    """

    metar_object: Metar = Metar(metar_report)
    return metar_object.get_visibility_category()


def test_ceiling_extraction(metar_report: str) -> int:
    """
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    10000
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 4SM BKN041 SCT030 23/14 A3001 RMK AO2 SLP165')
    4100
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 4SM BKN041 OVC030 23/14 A3001 RMK AO2 SLP165')
    3000
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 4SM SCT041 OVC030 23/14 A3001 RMK AO2 SLP165')
    3000
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 3SM SCT041 BKN025 23/14 A3001 RMK AO2 SLP165')
    2500
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 2 1/2SM SCT041 BKN009 23/14 A3001 RMK AO2 SLP165')
    900
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 2 1/2SM SCT041 OVC009 23/14 A3001 RMK AO2 SLP165')
    900
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 2SM OVC004 23/14 A3001 RMK AO2 SLP165')
    400
    >>> test_ceiling_extraction('KRNT 132053Z 33010KT 2SM SCT010 OVC004 23/14 A3001 RMK AO2 SLP165')
    400
    >>> test_ceiling_extraction('KGCC 231853Z AUTO 28011KT 20/12 A2991 RMK AO2 LTG DSNT SE RAB41RAEMM SLP085 P0000 T02000117 PWINO $')
    10000
    >>> test_ceiling_extraction('KVOK 251453Z 34004KT 10SM SCT008 OVC019 21/21 A2988 RMK AO2A SCT V BKN SLP119 53012')
    1900
    """
    metar_object: Metar = Metar(metar_report)
    return metar_object.get_ceiling()


def test_ceiling_categorization(metar_report: str) -> str:
    """
    >>> test_ceiling_categorization('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
    'VFR'
    >>> test_ceiling_categorization('KRNT 132053Z 33010KT 4SM SCT041 OVC030 23/14 A3001 RMK AO2 SLP165')
    'MVFR'
    >>> test_ceiling_categorization('KRNT 132053Z 33010KT 3SM SCT041 BKN025 23/14 A3001 RMK AO2 SLP165')
    'MVFR'
    >>> test_ceiling_categorization('KRNT 132053Z 33010KT 2 1/2SM SCT041 BKN009 23/14 A3001 RMK AO2 SLP165')
    'IFR'
    >>> test_ceiling_categorization('KRNT 132053Z 33010KT 2 1/2SM SCT041 OVC009 23/14 A3001 RMK AO2 SLP165')
    'IFR'
    >>> test_ceiling_categorization('KRNT 132053Z 33010KT 2SM OVC004 23/14 A3001 RMK AO2 SLP165')
    'LIFR'
    >>> test_ceiling_categorization('KRNT 132053Z 33010KT 2SM SCT010 OVC004 23/14 A3001 RMK AO2 SLP165')
    'LIFR'
    >>> test_ceiling_categorization('KGCC 231853Z AUTO 28011KT 20/12 A2991 RMK AO2 LTG DSNT SE RAB41RAEMM SLP085 P0000 T02000117 PWINO $')
    'VFR'
    >>> test_ceiling_categorization('KVOK 251453Z 34004KT 10SM SCT008 OVC019 21/21 A2988 RMK AO2A SCT V BKN SLP119 53012')
    'MVFR'
    """
    metar_object: Metar = Metar(metar_report)
    return metar_object.get_ceiling_category()


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
