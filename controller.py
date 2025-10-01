# Live Sectional Map controller
# Dylan Rush 2017
# Additional modifications:
#   2018-2020, John Marzulli
# dylanhrush.com
# Uses RPi.GPIO library: https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/
# Free for personal use. Prohibited for commercial without consent
#
# pip install Adafruit-GPIO
# pip install RPi-GPIO
# pip install pytest
# pip install Adafruit_WS2801
#
# Raspberry Pi
# Run 'raspi-config' and enable the SPI bus under Advanced
#
# Wiring the WS2801 :
# https://learn.adafruit.com/12mm-led-pixels/wiring
# https://tutorials-raspberrypi.com/how-to-control-a-raspberry-pi-ws2801-rgb-led-strip/
# Blue -> 5V Minus AND Pi GND (Physical Pi 25)
# Red -> 5V Plus
# Yellow -> Pin 19(Physical)/SPI MOSI
# Green -> Pin 23(Physical)/SCLK/SPI
#


import threading
import time
from datetime import datetime, timezone

import lib.colors
import lib.local_debug as local_debug
import renderer
from configuration import configuration, configuration_server
from data_sources import weather
from lib import logger, safe_logging
from lib.recurring_task import RecurringTask
from visualizers import visualizers

thread_lock_object = threading.Lock()


if not local_debug.is_debug():
    import RPi.GPIO as GPIO
    try:
        GPIO.setmode(GPIO.BOARD)
    except Exception:
        # ws281x causes an exception
        # when you try to set the board type
        pass

stations = configuration.get_airport_configs()
rgb_colors = lib.colors.get_colors()

renderer = renderer.get_renderer()


def update_weather_for_all_stations():
    """
    Updates the weather for all of the stations.
    This does not update the conditions or category.
    """

    weather.get_metars(stations.keys())


def __get_dimmed_color__(
    starting_color: list
) -> list:
    """
    Given a starting color, get the version that is dimmed.

    Arguments:
        starting_color {list} -- The starting color that will be dimmed.

    Returns:
        list -- The color with the dimming adjustment.
    """
    dimmed_color = []
    brightness_adjustment = configuration.get_brightness_proportion()
    for color in starting_color:
        reduced_color = float(color) * brightness_adjustment

        # Some colors are floats, some are integers.
        # Make sure we keep everything the same.
        if isinstance(color, int):
            reduced_color = int(reduced_color)

        dimmed_color.append(reduced_color)

    return dimmed_color


def all_stations(
    color: list
):
    """
    Sets all of the airports to the given color

    Arguments:
        color {triple} -- Three integer tuple(triple?) of the RGB values
        of the color to set for ALL airports.
    """

    [renderer.set_leds(stations[station], color)
        for station in stations]

    renderer.show()


def __all_leds_to_color__(
    color: list
):
    renderer.set_all(color)


def get_station_by_led(
    index: int
) -> str:
    """
    Given an LED, find the station it is representing.

    Args:
        index (int): [description]

    Returns:
        str: The identifier of the station.
    """
    for station_identifier in stations.keys():
        if index in stations[station_identifier]:
            return station_identifier

    return "UNK"


def render_thread():
    """
    Main logic loop for rendering the lights.
    """

    safe_logging.safe_log("Starting rendering thread")

    tic = time.perf_counter()
    toc = time.perf_counter()
    debug_pixels_timer = None

    loaded_visualizers = visualizers.VisualizerManager.initialize_visualizers(
        renderer,
        stations)
    last_visualizer = 0

    while True:
        try:
            delta_time = toc - tic

            tic = time.perf_counter()

            visualizer_index = configuration.get_visualizer_index(
                loaded_visualizers)

            if visualizer_index != last_visualizer:
                renderer.clear()
                last_visualizer = visualizer_index

            loaded_visualizers[visualizer_index].update(delta_time)

            show_debug_pixels = (
                debug_pixels_timer is None
                or (
                    datetime.now(timezone.utc) - debug_pixels_timer
                ).total_seconds()
                > 60.0
            )

            if show_debug_pixels:
                for index in range(renderer.pixel_count):
                    station = get_station_by_led(index)
                    safe_logging.safe_log(f'[{station}/{index}]={renderer.pixels[index]}')

                debug_pixels_timer = datetime.utcnow()

            toc = time.perf_counter()
        except KeyboardInterrupt:
            quit()
        except Exception as ex:
            safe_logging.safe_log(ex)


def wait_for_all_stations():
    """
    Waits for all of the airports to have been given a chance to initialize.
    If an airport had an error, then that still counts.
    """

    for airport in stations:
        try:
            weather.get_metar(airport)
        except Exception as ex:
            safe_logging.safe_log_warning(
                f"Error while initializing with airport={airport}, EX={ex}"
            )

    return True


def __get_test_cycle_colors__() -> list:
    base_colors_test = [
        lib.colors.MAGENTA,
        lib.colors.RED,
        lib.colors.BLUE,
        lib.colors.GREEN,
        lib.colors.YELLOW,
        lib.colors.WHITE,
        lib.colors.GRAY,
        lib.colors.DARK_YELLOW
    ]

    colors_to_init = []

    for color in base_colors_test:
        is_global_dimming = configuration.get_brightness_proportion() < 1.0
        color_to_cycle = rgb_colors[color]
        colors_to_init.append(color_to_cycle)
        if is_global_dimming:
            colors_to_init.append(__get_dimmed_color__(color_to_cycle))

    colors_to_init.append(rgb_colors[lib.colors.OFF])

    return colors_to_init


def __test_all_leds__():
    """
    Test all of the LEDs, independent of the configuration
    to make sure the wiring is correct and that none have failed.
    """
    for color in __get_test_cycle_colors__():
        safe_logging.safe_log(f"Setting to {color}")
        __all_leds_to_color__(color)
        time.sleep(0.5)


if __name__ == '__main__':
    # Start loading the METARs in the background
    # while going through the self-test
    safe_logging.safe_log("Initialize weather for all airports")

    weather.get_metars(stations.keys())

    __test_all_leds__()

    web_server = configuration_server.WeatherMapServer()

    all_stations(rgb_colors[lib.colors.OFF])

    RecurringTask(
        "rest_host",
        0.1,
        web_server.run,
        logger.LOGGER,
        True)

    wait_for_all_stations()

    while True:
        try:
            render_thread()
        except KeyboardInterrupt:
            break

    if not local_debug.is_debug():
        GPIO.cleanup()
