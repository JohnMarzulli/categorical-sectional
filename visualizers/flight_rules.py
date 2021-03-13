import lib.colors as colors_lib
from configuration import configuration
from data_sources import weather
from lib import colors as colors_lib
from lib import safe_logging
from renderers.debug import Renderer

from visualizers.visualizer import BlinkingVisualizer, rgb_colors


def get_airport_category(
    airport: str,
    metar: str
) -> str:
    """
    Gets the category of a single airport.

    Arguments:
        airport {string} -- The airport identifier.
        utc_offset {int} -- The offset from UTC to local for the airport.

    Returns:
        string -- The weather category for the airport.
    """
    category = weather.INVALID

    try:
        try:
            is_inop = weather.is_station_inoperative(metar)

            category = weather.INOP if is_inop\
                else weather.get_category(airport, metar)
        except Exception as e:
            safe_logging.safe_log_warning(
                "Exception while attempting to categorize METAR:{} EX:{}".format(metar, e))
    except Exception as e:
        safe_logging.safe_log(
            "Captured EX while attempting to get category for {} EX:{}".format(airport, e))
        category = weather.INVALID

    return category


def get_color_from_condition(
    category: str
) -> str:
    """
    From a condition, returns the color it should be rendered as, and if it should flash.

    Arguments:
        category {string} -- The weather category (VFR, IFR, et al.)

    Returns:
        [str] -- The color name that should be displayed.
    """

    if category == weather.VFR:
        return colors_lib.GREEN
    elif category == weather.MVFR:
        return colors_lib.BLUE
    elif category == weather.IFR:
        return colors_lib.RED
    elif category == weather.LIFR:
        return colors_lib.MAGENTA
    elif category == weather.NIGHT:
        return colors_lib.YELLOW
    elif category == weather.SMOKE:
        return colors_lib.WHITE

    # Error
    return colors_lib.OFF


def should_station_flash(
    metar: str
) -> bool:
    is_old = False
    metar_age = None

    if metar is not None and metar != weather.INVALID:
        metar_age = weather.get_metar_age(metar)

    if metar_age is not None:
        metar_age_minutes = metar_age.total_seconds() / 60.0
        is_old = metar_age_minutes > weather.DEFAULT_METAR_INVALIDATE_MINUTES
        is_inactive = metar_age_minutes > configuration.get_metar_station_inactive_minutes()
    else:
        is_inactive = True

    # No report for a while?
    # Count the station as INOP.
    # The default is to follow what ForeFlight and SkyVector
    # do and just turn it off.
    if is_inactive:
        return False

    should_blink = is_old and configuration.get_blink_station_if_old_data()

    return should_blink


def get_airport_condition(
    airport: str
) -> str:
    """
    Sets the given airport to have the given flight rules category.

    Arguments:
        airport {str} -- The airport identifier.
        category {string} -- The flight rules category.

    Returns:
        bool -- True if the flight category changed (or was set for the first time).
    """

    try:
        metar = weather.get_metar(airport)
        category = get_airport_category(airport, metar)
        should_flash = should_station_flash(metar)

        return category, should_flash
    except Exception as ex:
        safe_logging.safe_log_warning(
            'set_airport_display() - {} - EX:{}'.format(airport, ex))

        return weather.INOP, True


# VFR - Green
# MVFR - Blue
# IFR - Red
# LIFR - Flashing red
# Error - Flashing white


class FlightRulesVisualizer(BlinkingVisualizer):
    def __init__(
        self,
        renderer: Renderer,
        stations: dict,
    ):
        super().__init__(renderer, stations)

    def render_station(
        self,
        station: str,
        is_blink: bool = False
    ):
        """
        Sets the LED for a station.
        This is a default, empty, implementation meant to be overridden
        and simply define the interface.

        Args:
            renderer (Renderer): [description]
            airport (str): [description]
            is_blink (bool, optional): [description]. Defaults to False.
        """
        condition, blink = get_airport_condition(station)
        color_name_by_category = get_color_from_condition(condition)
        color_by_category = rgb_colors[color_name_by_category]

        if is_blink:
            metar = weather.get_metar(station)
            is_lightning = weather.is_lightning(metar)

            if is_lightning and configuration.get_lightning_blink():
                color_by_category = rgb_colors[colors_lib.YELLOW]

        if blink and is_blink:
            color_by_category = rgb_colors[colors_lib.OFF]

        color_to_render = self.__get_brightness_adjusted_color__(
            station,
            color_by_category)

        self.__renderer__.set_leds(
            self.__stations__[station],
            color_to_render)
