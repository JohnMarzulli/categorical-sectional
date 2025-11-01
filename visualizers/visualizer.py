import meteorology.types.classifications
from configuration import configuration
from data_sources import daylight
from lib import colors as colors_lib
from renderers.debug import Renderer

AVAILABLE_COLORS: dict[str, list] = colors_lib.get_colors()
__COLORS_BY_FLIGHT_RULE__: dict[str, list] = {
    meteorology.types.classifications.IFR: AVAILABLE_COLORS[colors_lib.RED],
    meteorology.types.classifications.VFR: AVAILABLE_COLORS[colors_lib.GREEN],
    meteorology.types.classifications.MVFR: AVAILABLE_COLORS[colors_lib.BLUE],
    meteorology.types.classifications.LIFR: AVAILABLE_COLORS[colors_lib.MAGENTA],
    meteorology.types.classifications.NIGHT: AVAILABLE_COLORS[colors_lib.YELLOW],
    meteorology.types.classifications.NIGHT_DARK: AVAILABLE_COLORS[
        colors_lib.DARK_YELLOW
    ],
    meteorology.types.classifications.SMOKE: AVAILABLE_COLORS[colors_lib.GRAY],
    meteorology.types.classifications.INVALID: AVAILABLE_COLORS[colors_lib.OFF],
    meteorology.types.classifications.INOP: AVAILABLE_COLORS[colors_lib.OFF],
}


def __get_rgb_night_color_to_render__(color_by_category, proportions):
    target_night_color = colors_lib.get_color_mix(
        AVAILABLE_COLORS[colors_lib.OFF],
        color_by_category,
        configuration.get_night_category_proportion(),
    )

    # For the scenario where we simply dim the LED to account for sunrise/sunset
    # then only use the period between sunset/sunrise start and civil twilight
    if proportions[0] > 0.0:
        return colors_lib.get_color_mix(
            color_by_category, target_night_color, proportions[0]
        )
    elif proportions[1] > 0.0:
        return colors_lib.get_color_mix(
            target_night_color, color_by_category, proportions[1]
        )
    else:
        return target_night_color


def __get_night_color_to_render__(color_by_category: list, proportions: list) -> list:
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

    color_to_render = AVAILABLE_COLORS[colors_lib.OFF]

    if proportions[0] <= 0.0 and proportions[1] <= 0.0:
        if configuration.get_night_populated_yellow():
            color_to_render = AVAILABLE_COLORS[colors_lib.DARK_YELLOW]
        else:
            color_to_render = __get_rgb_night_color_to_render__(
                color_by_category, proportions
            )
    # Do not allow color mixing for standard LEDs
    # Instead if we are going to render NIGHT then
    # have the NIGHT color represent that the station
    # is in a twilight period.
    elif configuration.get_mode() == configuration.STANDARD:
        if proportions[0] > 0.0 or proportions[1] < 1.0:
            color_to_render = __COLORS_BY_FLIGHT_RULE__[
                meteorology.types.classifications.NIGHT
            ]
        elif proportions[0] <= 0.0 and proportions[1] <= 0.0:
            color_to_render = AVAILABLE_COLORS[colors_lib.DARK_YELLOW]
    elif not configuration.get_night_populated_yellow():
        color_to_render = __get_rgb_night_color_to_render__(
            color_by_category, proportions
        )
    elif proportions[0] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            AVAILABLE_COLORS[colors_lib.DARK_YELLOW],
            __COLORS_BY_FLIGHT_RULE__[meteorology.types.classifications.NIGHT],
            proportions[0],
        )
    elif proportions[1] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            __COLORS_BY_FLIGHT_RULE__[meteorology.types.classifications.NIGHT],
            color_by_category,
            proportions[1],
        )

    return color_to_render


def __get_mix_and_color__(color_by_category, airport):
    """
    Gets the proportion of color mixes (dark to NIGHT, NIGHT to color) and the final color to render.

    Arguments:
        color_by_category {tuple} -- the initial color decided upon by weather.
        airport {string} -- The station identifier.

    Returns:
        tuple -- proportion, color to render
    """

    color_to_render = color_by_category
    proportions: list = daylight.get_twilight_transition(airport)

    if configuration.get_night_lights():
        color_to_render = __get_night_color_to_render__(color_by_category, proportions)

    brightness_adjustment = configuration.get_brightness_proportion()
    final_color = colors_lib.get_brightness_adjusted_color(
        color_to_render, brightness_adjustment
    )

    return proportions, final_color


class Visualizer(object):
    def __init__(self, renderer: Renderer, stations: dict):
        super().__init__()

        self.__renderer__ = renderer
        self.__stations__ = stations

    def __get_brightness_adjusted_color__(
        self, station: str, starting_color: list
    ) -> list:
        proportions, color_to_render = __get_mix_and_color__(starting_color, station)
        brightness_adjustment = configuration.get_brightness_proportion()
        return colors_lib.get_brightness_adjusted_color(
            color_to_render, brightness_adjustment
        )

    def get_name(self) -> str:
        """
        Get the name of the visualizer.

        Returns:
            str: The name of the visualizer.
        """
        return self.__class__.__name__

    def update(self, time_slice: float):
        """
        Default implementation that does not take any action.
        Simply there to define the interface.

        Args:
            renderer (Renderer): The renderer that will set the LEDs or debug info.
            time_slice (float): How long since the last call to update.
        """
        pass
