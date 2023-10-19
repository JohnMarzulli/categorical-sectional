import random
from datetime import datetime
from typing import Tuple

import lib.colors as colors_lib
from configuration import configuration
from data_sources import weather
from renderers.debug import Renderer

from visualizers.visualizer import BlinkingVisualizer


def celsius_to_fahrenheit(
    temperature_celsius: float
):
    """
    Converts a temperature in celsius to fahrenheit.

    Args:
        temperature_celsius (float): A temperature in C

    Returns:
        [type]: The temperature converted to F
    """
    if temperature_celsius is None:
        return 0

    return (temperature_celsius * (9.0 / 5.0)) + 32.0


def get_proportion_between_floats(
    start: float,
    current: float,
    end: float
):
    """
    Gets the "distance" (0.0 to 1.0) between the start and the end where the current is.
    IE:
        If the Current is the same as Start, then the result will be 0.0
        If the Current is the same as the End, then the result will be 1.0
        If the Current is halfway between Start and End, then the result will be 0.5


    Arguments:
        start {float} -- The starting temp.
        current {float} -- The temp we want to get the proportion for.
        end {float} -- The end temp to calculate the interpolaton for.

    Returns:
        float -- The amount of interpolaton for Current between Start and End
    """

    total_delta = (end - start)
    time_in = (current - start)

    return time_in / total_delta


def get_color_by_temperature_celsius(
    temperature_celsius: float
) -> list:
    """
    Given a temperature (in Celsius), return the color
    that should represent that temp on the map.

    These colors were decided based on weather temperature maps
    and thermometer markings.

    Args:
        temperature_celsius (float): A temperature in metric.

    Returns:
        list: The RGB color to show on the map.
    """
    colors_by_name = colors_lib.get_colors()

    if temperature_celsius is None:
        return colors_by_name[colors_lib.OFF]

    temperature_fahrenheit = celsius_to_fahrenheit(temperature_celsius)

    if temperature_fahrenheit < 0:
        return colors_by_name[colors_lib.PURPLE]

    if temperature_fahrenheit < 20:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.PURPLE],
            colors_by_name[colors_lib.BLUE],
            get_proportion_between_floats(
                0,
                temperature_fahrenheit,
                20))

    if temperature_fahrenheit < 40:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.BLUE],
            colors_by_name[colors_lib.GREEN],
            get_proportion_between_floats(
                20,
                temperature_fahrenheit,
                40))

    if temperature_fahrenheit < 60:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.GREEN],
            colors_by_name[colors_lib.YELLOW],
            get_proportion_between_floats(
                40,
                temperature_fahrenheit,
                60))

    if temperature_fahrenheit < 80:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.YELLOW],
            colors_by_name[colors_lib.ORANGE],
            get_proportion_between_floats(
                60,
                temperature_fahrenheit,
                80))

    if temperature_fahrenheit < 100:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.ORANGE],
            colors_by_name[colors_lib.RED],
            get_proportion_between_floats(
                80,
                temperature_fahrenheit,
                100))

    return colors_by_name[colors_lib.RED]


def get_twinkle_proportion() -> float:
    """
    Get a random proportion to cause likes to twinkle.

    Returns:
        float: A value between 0.0 and 1.0
    """
    value = random.random()

    return value


def get_pulse_interval_proportion(
    current_time: datetime,
    pulse_interval: float
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


def get_color_by_precipitation(
    precipitation: str,
    pulse_interval: float = 2.0
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

    if precipitation is weather.DRIZZLE:
        return (colors_by_name[colors_lib.LIGHT_BLUE], False)

    if weather.RAIN in precipitation:
        return (colors_by_name[colors_lib.BLUE], precipitation is weather.HEAVY_RAIN)

    if precipitation is weather.SNOW:
        # We want to make snow pulse
        # So lets interpolate the color
        # between "nothing" and snow
        # such that we use the seconds
        if configuration.get_snow_twinkle():
            proportion = get_twinkle_proportion()
        elif configuration.get_snow_pulse():
            proportion = get_pulse_interval_proportion(
                datetime.utcnow(),
                pulse_interval)
        else:
            proportion = 1.0

        color = colors_lib.get_color_mix(
            no_precip,
            snow_precip,
            proportion)

        return (color, False)

    if precipitation is weather.ICE:
        return (colors_by_name[colors_lib.LIGHT_GRAY], True)

    if precipitation is weather.UNKNOWN:
        return (colors_by_name[colors_lib.PURPLE], False)

    return (colors_by_name[colors_lib.GRAY], False)


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


def get_color_by_pressure(
    inches_of_mercury: float
) -> list:
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
            get_proportion_between_floats(
                STANDARD_PRESSURE,
                inches_of_mercury,
                HIGH_PRESSURE))

    return colors_lib.get_color_mix(
        colors_by_name[colors_lib.RED],
        colors_by_name[colors_lib.LIGHT_RED],
        get_proportion_between_floats(
            LOW_PRESSURE,
            inches_of_mercury,
            STANDARD_PRESSURE))


class TemperatureVisualizer(BlinkingVisualizer):
    def __init__(
        self,
        renderer: Renderer,
        stations: dict
    ):
        super().__init__(renderer, stations)

    def render_station(
        self,
        station: str,
        is_blink: bool = False
    ):
        """
        Renders an airport.

        Arguments:
            airport {string} -- The identifier of the station.
        """

        metar = weather.get_metar(station)
        temperature = weather.get_temperature(metar)
        color_to_render = get_color_by_temperature_celsius(temperature)
        final_color = self.__get_brightness_adjusted_color__(
            station,
            color_to_render)

        self.__renderer__.set_leds(
            self.__stations__[station],
            final_color)


class PrecipitationVisualizer(BlinkingVisualizer):

    def __init__(
        self,
        renderer: Renderer,
        stations: dict
    ):
        super().__init__(renderer, stations)

    def render_station(
        self,
        station: str,
        is_blink: bool = False
    ):
        """
        Renders a station based on any precipitation found in the metar.

        Arguments:
            station {string} -- The identifier of the station.
        """

        metar = weather.get_metar(station)
        precipitation = weather.get_precipitation(metar)
        color_to_render, blink = get_color_by_precipitation(precipitation)
        final_color = self.__get_brightness_adjusted_color__(
            station,
            color_to_render)

        # Turn the LED off for the blink
        if is_blink and blink:
            final_color = colors_lib.get_brightness_adjusted_color(
                final_color, 0.0)

        self.__renderer__.set_leds(
            self.__stations__[station],
            final_color)

    def __get_update_interval__(
        self
    ) -> float:
        # Immediate update
        return 0.0


class PressureVisualizer(BlinkingVisualizer):
    """
    Visualizer for pressure. High pressure is represented
    by BLUE while low pressure is represented by RED.
    """

    def __init__(
        self,
        renderer: Renderer,
        stations: dict
    ):
        super().__init__(renderer, stations)

    def render_station(
        self,
        station: str,
        is_blink: bool = False
    ):
        """
        Renders a station based on the pressure.

        Arguments:
            station {string} -- The identifier of the station.
        """

        metar = weather.get_metar(station)
        pressure = weather.get_pressure(metar)
        color_to_render = get_color_by_pressure(pressure)
        final_color = colors_lib.get_brightness_adjusted_color(
            color_to_render,
            configuration.get_brightness_proportion())

        self.__renderer__.set_leds(
            self.__stations__[station],
            final_color)
