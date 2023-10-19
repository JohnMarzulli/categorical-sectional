import time
from datetime import datetime

from configuration import configuration
from data_sources import weather
from lib import colors as colors_lib
from lib import safe_logging
from renderers.debug import Renderer

rgb_colors = colors_lib.get_colors()
color_by_rules = {
    weather.IFR: rgb_colors[colors_lib.RED],
    weather.VFR: rgb_colors[colors_lib.GREEN],
    weather.MVFR: rgb_colors[colors_lib.BLUE],
    weather.LIFR: rgb_colors[colors_lib.MAGENTA],
    weather.NIGHT: rgb_colors[colors_lib.YELLOW],
    weather.NIGHT_DARK: rgb_colors[colors_lib.DARK_YELLOW],
    weather.SMOKE: rgb_colors[colors_lib.GRAY],
    weather.INVALID: rgb_colors[colors_lib.OFF],
    weather.INOP: rgb_colors[colors_lib.OFF]
}


def __get_rgb_night_color_to_render__(
    color_by_category,
    proportions
):
    target_night_color = colors_lib.get_color_mix(
        rgb_colors[colors_lib.OFF],
        color_by_category,
        configuration.get_night_category_proportion())

    # For the scenario where we simply dim the LED to account for sunrise/sunset
    # then only use the period between sunset/sunrise start and civil twilight
    if proportions[0] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            color_by_category,
            target_night_color,
            proportions[0])
    elif proportions[1] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            target_night_color,
            color_by_category,
            proportions[1])
    else:
        color_to_render = target_night_color

    return color_to_render


def __get_night_color_to_render__(
    color_by_category: list,
    proportions: list
) -> list:
    """
    Calculate the color an airport should be based on the day/night cycle.
    Based on the configuration mixes the color with "Night Yellow" or dims the LEDs.
    A station that is in full daylight will be its normal color.
    A station that is in full darkness with be Night Yellow or dimmed to the night level.
    A station that is in sunset or sunrise will be mixed appropriately.

    Arguments:
        color_by_category {list} -- [description]
        proportions {list} -- [description]

    Returns:
        list -- [description]
    """

    color_to_render = weather.INOP

    if proportions[0] <= 0.0 and proportions[1] <= 0.0:
        if configuration.get_night_populated_yellow():
            color_to_render = rgb_colors[colors_lib.DARK_YELLOW]
        else:
            color_to_render = __get_rgb_night_color_to_render__(
                color_by_category,
                proportions)
    # Do not allow color mixing for standard LEDs
    # Instead if we are going to render NIGHT then
    # have the NIGHT color represent that the station
    # is in a twilight period.
    elif configuration.get_mode() == configuration.STANDARD:
        if proportions[0] > 0.0 or proportions[1] < 1.0:
            color_to_render = color_by_rules[weather.NIGHT]
        elif proportions[0] <= 0.0 and proportions[1] <= 0.0:
            color_to_render = rgb_colors[colors_lib.DARK_YELLOW]
    elif not configuration.get_night_populated_yellow():
        color_to_render = __get_rgb_night_color_to_render__(
            color_by_category,
            proportions)
    elif proportions[0] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            rgb_colors[colors_lib.DARK_YELLOW],
            color_by_rules[weather.NIGHT],
            proportions[0])
    elif proportions[1] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            color_by_rules[weather.NIGHT],
            color_by_category,
            proportions[1])

    return color_to_render


def get_mix_and_color(
    color_by_category,
    airport
):
    """
    Gets the proportion of color mixes (dark to NIGHT, NIGHT to color) and the final color to render.

    Arguments:
        color_by_category {tuple} -- the initial color decided upon by weather.
        airport {string} -- The station identifier.

    Returns:
        tuple -- proportion, color to render
    """

    color_to_render = color_by_category
    proportions = weather.get_twilight_transition(airport)

    if configuration.get_night_lights():
        color_to_render = __get_night_color_to_render__(
            color_by_category,
            proportions)

    brightness_adjustment = configuration.get_brightness_proportion()
    final_color = colors_lib.get_brightness_adjusted_color(
        color_to_render,
        brightness_adjustment)

    return proportions, final_color


class Visualizer(object):
    def __init__(
        self,
        renderer: Renderer,
        stations: dict
    ):
        super().__init__()

        self.__renderer__ = renderer
        self.__stations__ = stations

    def __get_brightness_adjusted_color__(
        self,
        station: str,
        starting_color: list
    ) -> list:
        proportions, color_to_render = get_mix_and_color(
            starting_color,
            station)
        brightness_adjustment = configuration.get_brightness_proportion()
        final_color = colors_lib.get_brightness_adjusted_color(
            color_to_render,
            brightness_adjustment)

        return final_color

    def get_name(
        self
    ) -> str:
        """
        Get the name of the visualizer.

        Returns:
            str: The name of the visualizer.
        """
        return self.__class__.__name__

    def update(
        self,
        time_slice: float
    ):
        """
        Default implementation that does not take any action.
        Simply there to define the interface.

        Args:
            renderer (Renderer): The renderer that will set the LEDs or debug info.
            time_slice (float): How long since the last call to update.
        """
        pass


class BlinkingVisualizer(Visualizer):
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
        Sets the LED for a station.
        This is a default, empty, implementation meant to be overridden
        and simply define the interface.

        Args:
            renderer (Renderer): [description]
            airport (str): [description]
            is_blink (bool, optional): [description]. Defaults to False.
        """
        pass

    def render_station_displays(
        self,
        is_blink: bool
    ) -> float:
        """
        Sets the LEDs for all of the airports based on their flight rules.
        Does this independent of the LED type.

        Arguments:
            is_blink {bool} -- Is this on the "off" cycle of blinking.
        """

        start_time = datetime.utcnow()

        for station in self.__stations__:
            try:
                self.render_station(
                    station,
                    is_blink)
            except Exception as ex:
                safe_logging.safe_log_warning(
                    'Catch-all error in render_station_displays of {} EX={}'.format(
                        station,
                        ex))

        self.__renderer__.show()

        return (datetime.utcnow() - start_time).total_seconds()

    def update(
        self,
        time_slice: float
    ):
        for is_blink in [True, False]:
            render_time = self.render_station_displays(
                is_blink)

            time_to_sleep = self.__get_update_interval__() - render_time

            if time_to_sleep > 0.0:
                time.sleep(time_to_sleep)

    def __get_update_interval__(
        self
    ) -> float:
        return 1.0
