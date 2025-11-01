import lib.colors as colors_lib
import meteorology.types.classifications
from configuration import configuration
from data_sources import weather
from lib import colors as colors_lib
from lib import safe_logging
from meteorology.types.metar import Metar
from renderers.debug import Renderer
from visualizers.blinking_visualizer import BlinkingVisualizer
from visualizers.visualizer import AVAILABLE_COLORS


def get_airport_category(airport: str, metar: Metar) -> str:
    """
    Gets the category of a single airport.

    Arguments:
        airport {string} -- The airport identifier.
        utc_offset {int} -- The offset from UTC to local for the airport.

    Returns:
        string -- The weather category for the airport.
    """
    category = meteorology.types.classifications.INVALID

    try:
        try:
            is_inop = metar is None or not metar.is_valid()
            category = (
                meteorology.types.classifications.INOP
                if is_inop
                else metar.get_category()
            )
        except Exception as e:
            safe_logging.safe_log_warning(
                f"Exception while attempting to categorize METAR:{metar} EX:{e}"
            )
    except Exception as e:
        safe_logging.safe_log(
            f"Captured EX while attempting to get category for {airport} EX:{e}"
        )
        category = meteorology.types.classifications.INVALID

    return category


def get_color_from_condition(category: str) -> str:
    """
    From a condition, returns the color it should be rendered as, and if it should flash.

    Arguments:
        category {string} -- The weather category (VFR, IFR, et al.)

    Returns:
        [str] -- The color name that should be displayed.
    """

    if category == meteorology.types.classifications.VFR:
        return colors_lib.GREEN
    elif category == meteorology.types.classifications.MVFR:
        return colors_lib.BLUE
    elif category == meteorology.types.classifications.IFR:
        return colors_lib.RED
    elif category == meteorology.types.classifications.LIFR:
        return colors_lib.MAGENTA
    elif category == meteorology.types.classifications.NIGHT:
        return colors_lib.YELLOW
    elif category == meteorology.types.classifications.SMOKE:
        return colors_lib.WHITE

    # Error
    return colors_lib.OFF


def should_station_flash(metar: Metar) -> bool:
    is_old = False
    metar_age = None

    if metar is not None and metar != meteorology.types.classifications.INVALID:
        metar_age = metar.get_age()

    if metar_age is not None:
        metar_age_minutes = metar_age.total_seconds() / 60.0
        is_old = metar_age_minutes > weather.DEFAULT_METAR_INVALIDATE_MINUTES
        is_inactive = (
            metar_age_minutes > configuration.get_metar_station_inactive_minutes()
        )
    else:
        is_inactive = True

    # No report for a while?
    # Count the station as INOP.
    # The default is to follow what ForeFlight and SkyVector
    # do and just turn it off.
    if is_inactive:
        return False

    return is_old and configuration.get_blink_station_if_old_data()


def get_airport_condition(airport: str) -> tuple[str, bool]:
    """
    Sets the given airport to have the given flight rules category.

    Arguments:
        airport {str} -- The airport identifier.
        category {string} -- The flight rules category.

    Returns:
        bool -- True if the flight category changed (or was set for the first time).
    """

    try:
        metar: Metar = weather.get_metar(airport)
        category = (
            meteorology.types.classifications.INVALID
            if metar is None
            else metar.get_category()
        )
        should_flash = False if metar is None else should_station_flash(metar)

        return category, should_flash
    except Exception as ex:
        safe_logging.safe_log_warning(f"set_airport_display() - {airport} - EX:{ex}")

        return (meteorology.types.classifications.INOP, True)


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

    def render_station(self, station: str, is_blink: bool = False):
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
        color_by_category = AVAILABLE_COLORS[color_name_by_category]

        if is_blink:
            metar = weather.get_metar(station)
            is_lightning = False if metar is None else metar.has_lightning()

            if is_lightning:
                color_by_category = AVAILABLE_COLORS[colors_lib.YELLOW]

        if blink and is_blink:
            color_by_category = AVAILABLE_COLORS[colors_lib.OFF]

        color_to_render: list[int] = self.__get_brightness_adjusted_color__(
            station, color_by_category
        )

        self.__renderer__.set_leds(self.__stations__[station], color_to_render)
