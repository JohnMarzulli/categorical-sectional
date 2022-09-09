# Live Sectional Map controller
# Dylan Rush 2017
# Additional modifications:
#   2018-2020, John Marzulli
#   2022, Darryl Quinn
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
from datetime import datetime

import lib.colors as colors_lib
import lib.local_debug as local_debug
import renderer
from configuration import configuration, configuration_server
from data_sources import weather
from lib import colors as colors_lib
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
rgb_colors = colors_lib.get_colors()

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

    [renderer.set_leds(stations[station], rgb_colors[color])
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
    display = True

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

            on_time = configuration.get_on_time()
            #safe_logging.safe_log("on_time= {} type is {}".format(on_time, type(on_time)))
            off_time = configuration.get_off_time()
            #safe_logging.safe_log("off_time= {} type is {}".format(off_time, type(off_time)))

            if not (on_time is None or off_time is None):
                current_time = int(datetime.now().strftime("%H%M"))
                #safe_logging.safe_log('Current/On/Off times: {} / {} / {}'.format(current_time, on_time, off_time))
                if int(on_time) <= current_time < int(off_time):
                    if display is False:
                        safe_logging.safe_log('Waking up at {} until {}'.format(current_time, off_time))
                    display = True
                else:
                    if display is True:
                        safe_logging.safe_log('Going to sleep at {} until {}'.format(current_time, on_time))
                    display = False

            if display:
                loaded_visualizers[visualizer_index].update(delta_time)
            else:
                all_stations(colors_lib.OFF)
                time.sleep(10.0)

            show_debug_pixels = debug_pixels_timer is None or (
                datetime.utcnow() - debug_pixels_timer).total_seconds() > 60.0

            if show_debug_pixels:
                for index in range(renderer.pixel_count):
                    station = get_station_by_led(index)
                    safe_logging.safe_log('[{}/{}]={}'.format(
                        station,
                        index,
                        renderer.pixels[index]))

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
                "Error while initializing with airport={}, EX={}".format(airport, ex))

    return True


def __get_test_cycle_colors__() -> list:
    base_colors_test = [
        colors_lib.MAGENTA,
        colors_lib.RED,
        colors_lib.BLUE,
        colors_lib.GREEN,
        colors_lib.YELLOW,
        colors_lib.WHITE,
        colors_lib.GRAY,
        colors_lib.DARK_YELLOW
    ]

    colors_to_init = []

    for color in base_colors_test:
        is_global_dimming = configuration.get_brightness_proportion() < 1.0
        color_to_cycle = rgb_colors[color]
        colors_to_init.append(color_to_cycle)
        if is_global_dimming:
            colors_to_init.append(__get_dimmed_color__(color_to_cycle))

    colors_to_init.append(rgb_colors[colors_lib.OFF])

    return colors_to_init


def __test_all_leds__():
    """
    Test all of the LEDs, independent of the configuration
    to make sure the wiring is correct and that none have failed.
    """
    for color in __get_test_cycle_colors__():
        safe_logging.safe_log("Setting to {}".format(color))
        __all_leds_to_color__(color)
        time.sleep(0.5)


if __name__ == '__main__':
    # Start loading the METARs in the background
    # while going through the self-test
    safe_logging.safe_log("Initialize weather for all airports")

    weather.get_metars(stations.keys())

    __test_all_leds__()

    web_server = configuration_server.WeatherMapServer()

    all_stations(weather.OFF)

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
