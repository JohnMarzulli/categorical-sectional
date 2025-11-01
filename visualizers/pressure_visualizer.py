import lib.colors as colors_lib
import lib.interpolation as interpolation
from configuration import configuration
from data_sources import weather
from lib import colors as colors_lib
from meteorology.types.metar import Metar
from renderers.debug import Renderer
from visualizers.blinking_visualizer import BlinkingVisualizer

# Standard pressure is 29.92,
# so the upper limits were picked with
# the standard value in the middle.
#
# The "high pressure" value was picked
# based on what people perceive to be high pressure
# and from that the low pressure value was picked.
#
# Per:
#   https://weather.com/sports-recreation/fishing/news/fishing-barometer-20120328
#   https://www.quora.com/Is-30-a-high-barometric-pressure

HIGH_PRESSURE = 30.2
STANDARD_PRESSURE = 29.92
LOW_PRESSURE = 29.8


def __get_color_by_pressure__(inches_of_mercury: float) -> list:
    """
    Given a barometer reading, return a RGB color to show on the map.

    Args:
        inches_of_mercury (float): The barometer reading from a metar in inHg.

    Returns:
        list: The RGB color to show on the map for the station.
    """

    colors_by_name = colors_lib.get_colors()

    if inches_of_mercury is None:
        return colors_by_name[colors_lib.OFF]

    if inches_of_mercury < LOW_PRESSURE:
        return colors_by_name[colors_lib.RED]

    if inches_of_mercury > HIGH_PRESSURE:
        return colors_by_name[colors_lib.BLUE]

    if inches_of_mercury > STANDARD_PRESSURE:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.LIGHT_BLUE],
            colors_by_name[colors_lib.BLUE],
            interpolation.get_proportion_between_floats(
                STANDARD_PRESSURE, inches_of_mercury, HIGH_PRESSURE
            ),
        )

    return colors_lib.get_color_mix(
        colors_by_name[colors_lib.RED],
        colors_by_name[colors_lib.LIGHT_RED],
        interpolation.get_proportion_between_floats(
            LOW_PRESSURE, inches_of_mercury, STANDARD_PRESSURE
        ),
    )


class PressureVisualizer(BlinkingVisualizer):
    """
    Visualizer for pressure. High pressure is represented
    by BLUE while low pressure is represented by RED.
    """

    def __init__(self, renderer: Renderer, stations: dict):
        super().__init__(renderer, stations)

    def render_station(self, station: str, is_blink: bool = False):
        """
        Renders a station based on the pressure.

        Arguments:
            station {string} -- The identifier of the station.
        """

        metar: Metar = weather.get_metar(station)

        if metar is None:
            return

        pressure = metar.get_pressure()
        color_to_render = __get_color_by_pressure__(pressure)
        final_color = colors_lib.get_brightness_adjusted_color(
            color_to_render, configuration.get_brightness_proportion()
        )

        self.__renderer__.set_leds(self.__stations__[station], final_color)
