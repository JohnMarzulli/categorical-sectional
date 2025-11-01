import lib.colors as colors_lib
import lib.interpolation as interpolation
from data_sources import weather
from meteorology.temperature import celsius_to_fahrenheit
from meteorology.types.metar import Metar
from renderers.debug import Renderer
from visualizers.blinking_visualizer import BlinkingVisualizer


def get_color_by_temperature_celsius(temperature_celsius: float) -> list:
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
            interpolation.get_proportion_between_floats(0, temperature_fahrenheit, 20),
        )

    if temperature_fahrenheit < 40:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.BLUE],
            colors_by_name[colors_lib.GREEN],
            interpolation.get_proportion_between_floats(20, temperature_fahrenheit, 40),
        )

    if temperature_fahrenheit < 60:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.GREEN],
            colors_by_name[colors_lib.YELLOW],
            interpolation.get_proportion_between_floats(40, temperature_fahrenheit, 60),
        )

    if temperature_fahrenheit < 80:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.YELLOW],
            colors_by_name[colors_lib.ORANGE],
            interpolation.get_proportion_between_floats(60, temperature_fahrenheit, 80),
        )

    if temperature_fahrenheit < 100:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.ORANGE],
            colors_by_name[colors_lib.RED],
            interpolation.get_proportion_between_floats(
                80, temperature_fahrenheit, 100
            ),
        )

    return colors_by_name[colors_lib.RED]


class TemperatureVisualizer(BlinkingVisualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        super().__init__(renderer, stations)

    def render_station(self, station: str, is_blink: bool = False):
        """
        Renders an airport.

        Arguments:
            airport {string} -- The identifier of the station.
        """

        metar: Metar = weather.get_metar(station)
        if metar is None:
            return

        temperature = metar.get_temperature()
        color_to_render = get_color_by_temperature_celsius(temperature)
        final_color = self.__get_brightness_adjusted_color__(station, color_to_render)

        self.__renderer__.set_leds(self.__stations__[station], final_color)
