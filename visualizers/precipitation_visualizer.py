import random
from datetime import datetime
from typing import Tuple

import lib.colors as colors_lib
import meteorology.types.classifications
from configuration import configuration
from data_sources import weather
from lib import colors as colors_lib
from meteorology.types.metar import Metar
from renderers.debug import Renderer
from visualizers.blinking_visualizer import BlinkingVisualizer


def __get_color_by_precipitation__(
    precipitation: str, pulse_interval: float = 2.0
) -> Tuple[list, bool]:
    """
    Given a precipitation category, return a color
    to show on the map.

    Args:
        precipitation (str): The precipitation category.

    Returns:
        (list, bool): A tuple of the RGB color AND if the station should be blinking
    """

    colors_by_name = colors_lib.get_colors()

    no_precip = colors_by_name[colors_lib.GRAY]
    snow_precip = colors_by_name[colors_lib.WHITE]

    if precipitation is None:
        return (no_precip, False)

    if precipitation is meteorology.types.classifications.DRIZZLE:
        return (colors_by_name[colors_lib.LIGHT_BLUE], False)

    if meteorology.types.classifications.RAIN in precipitation:
        return (
            colors_by_name[colors_lib.BLUE],
            precipitation is meteorology.types.classifications.HEAVY_RAIN,
        )

    if precipitation is meteorology.types.classifications.SNOW:
        # We want to make snow pulse
        # So lets interpolate the color
        # between "nothing" and snow
        # such that we use the seconds
        if configuration.get_snow_twinkle():
            proportion = __get_twinkle_proportion__()
        elif configuration.get_snow_pulse():
            proportion = __get_pulse_interval_proportion__(
                datetime.utcnow(), pulse_interval
            )
        else:
            proportion = 1.0

        color = colors_lib.get_color_mix(no_precip, snow_precip, proportion)

        return (color, False)

    if precipitation is meteorology.types.classifications.ICE:
        return (colors_by_name[colors_lib.LIGHT_GRAY], True)

    if precipitation is meteorology.types.classifications.UNKNOWN:
        return (colors_by_name[colors_lib.PURPLE], False)

    return (colors_by_name[colors_lib.GRAY], False)


def __get_twinkle_proportion__() -> float:
    """
    Get a random proportion to cause likes to twinkle.

    Returns:
        float: A value between 0.0 and 1.0
    """
    return random.random()


def __get_pulse_interval_proportion__(
    current_time: datetime, pulse_interval: float
) -> float:
    """
    Get a value that causes the snow to pulse bright to dim.

    Args:
        current_time (datetime): The current time. Used to figure out where in the pulse we are.
        pulse_interval (float): How long a complete pulse takes.

    Returns:
        float: A value between 0.2 and 1.0
    """
    seconds = current_time.second + (current_time.microsecond / 1000000.0)
    seconds_in_interval = seconds % pulse_interval
    half_interval = pulse_interval / 2.0

    proportion = seconds_in_interval / half_interval

    if proportion >= 1.0:
        # 1.2 to 0.2
        proportion = proportion - 1.0
        # 0.2 to 0.8
        proportion = 1.0 - proportion

    return proportion


class PrecipitationVisualizer(BlinkingVisualizer):

    def __init__(self, renderer: Renderer, stations: dict):
        super().__init__(renderer, stations)

    def render_station(self, station: str, is_blink: bool = False):
        """
        Renders a station based on any precipitation found in the metar.

        Arguments:
            station {string} -- The identifier of the station.
        """

        metar: Metar | None = weather.get_metar(station)

        if metar is None:
            return

        precipitation = metar.get_precipitation()

        if precipitation is None:
            return

        color_to_render, blink = __get_color_by_precipitation__(precipitation)
        final_color = self.__get_brightness_adjusted_color__(station, color_to_render)

        # Turn the LED off for the blink
        if is_blink and blink:
            final_color = colors_lib.get_brightness_adjusted_color(final_color, 0.0)

        self.__renderer__.set_leds(self.__stations__[station], final_color)

    def __get_update_interval__(self) -> float:
        # Immediate update
        return 0.0
