from datetime import datetime, timezone

from data_sources.daylight import get_proportion_between_times
from meteorology.types.metar import Metar


def test_time_interpolation(
    start_time: datetime, current_time: datetime, end_time: datetime
) -> float:
    """
    >>> test_time_interpolation(datetime(2020, 10, 1), datetime(2020, 10, 1), datetime(2020, 10, 31))
    0.0
    >>> test_time_interpolation(datetime(2020, 10, 1), datetime(2020, 10, 2), datetime(2020, 10, 31))
    0.033
    >>> test_time_interpolation(datetime(2020, 10, 1), datetime(2020, 10, 15), datetime(2020, 10, 31))
    0.467
    >>> test_time_interpolation(datetime(2020, 10, 1), datetime(2020, 10, 30), datetime(2020, 10, 31))
    0.967
    >>> test_time_interpolation(datetime(2020, 10, 1), datetime(2020, 10, 31), datetime(2020, 10, 31))
    1.0
    >>> test_time_interpolation(datetime(2020, 10, 15), datetime(2020, 10, 1), datetime(2020, 10, 31))
    0.0
    >>> test_time_interpolation(datetime(2020, 10, 1), datetime(2020, 10, 31), datetime(2020, 10, 15))
    1.0
    """
    return round(get_proportion_between_times(start_time, current_time, end_time), 3)


def test_get_station_from_metar(metar_report: str) -> str:
    """
    >>> test_get_station_from_metar("")
    'INVALID'
    >>> test_get_station_from_metar('')
    'INVALID'
    >>> test_get_station_from_metar(None)
    'INVALID'
    >>> test_get_station_from_metar("asdasdasdasdasd")
    >>> test_get_station_from_metar("KBVS")
    'KBVS'
    >>> test_get_station_from_metar("KBVS 121955Z AUTO 00000KT 2SM BR CLR 17/15 A3001 RMK A01")
    'KBVS'
    >>> test_get_station_from_metar("KUIL 121953Z AUTO 00000KT 1 1/4SM HZ OVC021 14/11 A3000 RMK AO2 SLP158 T01440111")
    'KUIL'
    >>> test_get_station_from_metar("KHQM 121953Z AUTO 13004KT 1 1/2SM HZ BKN020 OVC028 16/12 A2999 RMK AO2 SLP160 T01610122")
    'KHQM'
    >>> test_get_station_from_metar("KAST 121955Z AUTO 01005KT 1 1/4SM HZ BKN025 OVC033 16/12 A2998 RMK AO2 SLP150 T01610122")
    'KAST'
    >>> test_get_station_from_metar("KPDX 121953Z 00000KT 3/4SM R10R/5000FT HZ BR VV014 15/11 A2999 RMK AO2 SLP155 T01500106")
    'KPDX'
    >>> test_get_station_from_metar("KSEA 121953Z 22003KT 3/4SM FU OVC006 13/11 A3001 RMK AO2 SLPNO FU OVC006 T01280111")
    'KSEA'
    >>> test_get_station_from_metar("KAWO 121956Z AUTO 12003KT 1 1/2SM BR CLR 14/12 A3001 RMK AO2 SLP167 T01440122")
    'KAWO'
    """

    metar: Metar = Metar(metar_report)

    return metar.get_station()


def test_get_metar_timestamp(metar_report: str) -> datetime:
    """
    >>> test_get_metar_timestamp("KBVS 121955Z AUTO 00000KT 2SM BR CLR 17/15 A3001 RMK A01")
    datetime.datetime(2025, 10, 12, 19, 55, tzinfo=datetime.timezone.utc)
    >>> test_get_metar_timestamp("KUIL 121953Z AUTO 00000KT 1 1/4SM HZ OVC021 14/11 A3000 RMK AO2 SLP158 T01440111")
    datetime.datetime(2025, 10, 12, 19, 53, tzinfo=datetime.timezone.utc)
    >>> test_get_metar_timestamp("KHQM 121953Z AUTO 13004KT 1 1/2SM HZ BKN020 OVC028 16/12 A2999 RMK AO2 SLP160 T01610122")
    datetime.datetime(2025, 10, 12, 19, 53, tzinfo=datetime.timezone.utc)
    >>> test_get_metar_timestamp("KAST 121955Z AUTO 01005KT 1 1/4SM HZ BKN025 OVC033 16/12 A2998 RMK AO2 SLP150 T01610122")
    datetime.datetime(2025, 10, 12, 19, 55, tzinfo=datetime.timezone.utc)
    >>> test_get_metar_timestamp("KPDX 121953Z 00000KT 3/4SM R10R/5000FT HZ BR VV014 15/11 A2999 RMK AO2 SLP155 T01500106")
    datetime.datetime(2025, 10, 12, 19, 53, tzinfo=datetime.timezone.utc)
    >>> test_get_metar_timestamp("KSEA 121953Z 22003KT 3/4SM FU OVC006 13/11 A3001 RMK AO2 SLPNO FU OVC006 T01280111")
    datetime.datetime(2025, 10, 12, 19, 53, tzinfo=datetime.timezone.utc)
    >>> test_get_metar_timestamp("KAWO 121956Z AUTO 12003KT 1 1/2SM BR CLR 14/12 A3001 RMK AO2 SLP167 T01440122")
    datetime.datetime(2025, 10, 12, 19, 56, tzinfo=datetime.timezone.utc)
    """
    metar: Metar = Metar(metar_report)

    return (
        metar.get_timestamp()
        if metar is not None
        else datetime.min.replace(tzinfo=timezone.utc)
    )


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
