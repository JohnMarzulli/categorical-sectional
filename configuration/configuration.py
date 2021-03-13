"""
Handles configuration loading and constants.
"""
import json
import os
import threading
import unicodedata
from pathlib import Path

from lib import local_debug
from lib.safe_logging import safe_log, safe_log_warning

if local_debug.is_debug():
    HIGH = 1
    LOW = 0
else:
    import RPi.GPIO as GPIO
    HIGH = GPIO.HIGH
    LOW = GPIO.LOW

# TODO - Change the relative pathing of the Airports files into an absolute path so when a config is written the to use dir the pathing still works.
# TODO - Implement file uploading WITH FILE NAME and then write that to the user directory.... with the correct pathing.

# Modes
STANDARD = 'led'
WS2801 = 'ws2801'
WS281x = 'ws281x'

LED_MODE_KEY = "mode"
PIXEL_COUNT_KEY = "pixel_count"
SPI_DEVICE_KEY = "spi_device"
SPI_PORT_KEY = "spi_port"
GPIO_PIN_KEY = "gpio_pin"
AIRPORTS_FILE_KEY = "airports_file"
BLINK_OLD_STATIONS_KEY = "blink_old_stations"
SNOW_PULSE_KEY = "snow_pulse"
SNOW_TWINKLE_KEY = "snow_twinkle"
NIGHT_LIGHTS_KEY = "night_lights"
LIGHTNING_BLINK_KEY = "lightning_blink"
NIGHT_POPULATED_YELLOW_KEY = "night_populated_yellow"
NIGHT_CATEGORY_PROPORTION_KEY = "night_category_proportion"
BRIGHTNESS_PROPORTION_KEY = "brightness_proportion"
VISUALIZER_INDEX_KEY = "visualizer"
PIXEL_ORDER_KEY = "pixel_order"
PIXEL_ORDER_DEFAULT = "GRB"

METAR_STATION_INACTIVE_MINUTES_KEY = "metar_station_inactive_minutes"
DEFAULT_METAR_STATION_INACTIVE_MINUTES = 3 * 60

__VALID_KEYS__ = [
    LED_MODE_KEY,
    PIXEL_COUNT_KEY,
    SPI_DEVICE_KEY,
    SPI_PORT_KEY,
    AIRPORTS_FILE_KEY,
    BLINK_OLD_STATIONS_KEY,
    NIGHT_LIGHTS_KEY,
    NIGHT_POPULATED_YELLOW_KEY,
    NIGHT_CATEGORY_PROPORTION_KEY,
    LIGHTNING_BLINK_KEY,
    SNOW_PULSE_KEY,
    SNOW_TWINKLE_KEY,
    BRIGHTNESS_PROPORTION_KEY,
    VISUALIZER_INDEX_KEY,
    PIXEL_ORDER_KEY,
    METAR_STATION_INACTIVE_MINUTES_KEY
]

__VALID_PIXEL_ORDERS__ = [
    "RGB",
    "GRB"
]

__DEFAULT_CONFIG_FILE__ = '../data/config.json'
__USER_CONFIG_FILE__ = '~/weather_map/config.json'

__lock__ = threading.Lock()


def __get_resolved_filepath__(
    filename: str
) -> str:
    """
    Try to resolve a filename to the proper full path.
    Used to help resolve relative path issues and issues with the working path when started from crontab.

    Arguments:
        filename {str} -- The filename (optionally with a partial path) to resolve to a fully qualified file path.

    Returns:
        str -- The fully resolved filepath
    """

    safe_log("Attempting to resolve '{}'".format(filename))
    safe_log("__file__='{}'".format(__file__))

    try:
        raw_path = filename

        if './' in filename:
            raw_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                filename)
        else:
            safe_log("Attempting to expand user pathing.")
            raw_path = Path(os.path.expanduser(filename))

            raw_path = str(raw_path)

        safe_log("Before normalization path='{}'".format(raw_path))

        normalized_path = os.path.normpath(raw_path)

        safe_log("Normalized path='{}'".format(raw_path))

        return normalized_path
    except Exception as ex:
        safe_log(
            "__get_resolved_filepath__:Attempted to resolve. got EX={}".format(ex))
        return None


def __load_config_file__(
    config_filename: str
) -> dict:
    """
    Loads a configuration file from the given source.

    Arguments:
        config_filename {str} -- The path to the configuration file to load.

    Returns:
        dict -- Any given configuration found.
    """
    try:
        full_filename = __get_resolved_filepath__(config_filename)

        with open(str(full_filename)) as config_file:
            config_text = config_file.read()
            loaded_configuration = json.loads(config_text)

            configuration = {}

            for config_key in loaded_configuration.keys():
                value = loaded_configuration[config_key]

                if value is not None:
                    configuration[config_key] = value

            return configuration
    except Exception as ex:
        safe_log_warning(
            "Error while trying to load {}: EX={}".format(config_filename, ex))
        return {}


def __get_configuration__() -> dict:
    """
    Loads the default configuration. Then loads any user configuration and applies the new data over the defaults.

    Returns:
        dict -- The default configuration with the user changes applied over top.
    """
    configuration = __load_config_file__(__DEFAULT_CONFIG_FILE__)
    user_configuration = __load_config_file__(__USER_CONFIG_FILE__)

    configuration.update(user_configuration)

    return configuration


CONFIG = __get_configuration__()


def __write_user_configuration__(
    config: dict
) -> bool:
    """
    Writes the current configuration to the user directory.

    Returns:
        bool -- True if the configuration was written to disk
    """
    try:
        safe_log("Starting to write file.")

        full_filename = None

        try:
            full_filename = __get_resolved_filepath__(__USER_CONFIG_FILE__)
            safe_log("full_filename=`{}`".format(full_filename))
        except Exception:
            pass

        if full_filename is None:
            safe_log("Unable to resolve, using relative path + name instead.")
            full_filename = __USER_CONFIG_FILE__

        directory = os.path.dirname(full_filename)
        safe_log("directory=`{}`".format(directory))

        if not os.path.exists(directory):
            try:
                safe_log("Attempting to create directory `{}`".format(directory))
                os.mkdir(directory)
            except Exception as ex:
                safe_log("While attempting to create directory, EX={}".format(ex))

        with open(str(full_filename), "w") as config_file:
            safe_log("Opened `{}` for write.".format(full_filename))

            config_text = json.dumps(config, indent=4, sort_keys=True)
            safe_log("config_text=`{}`".format(config_text))

            config_file.write(config_text)

            safe_log("Finished writing file.")

            return True
    except Exception as ex:
        safe_log(
            "Error while trying to write {}: EX={}".format(
                __USER_CONFIG_FILE__,
                ex))
        return False


def update_configuration(
    new_config: dict
) -> dict:
    """
    Given a new piece of configuration, update it gracefully.

    Arguments:
        new_config {dict} -- The new configuration... partial or whole.

    Returns:
        dict -- The updated configuration.
    """
    if new_config is None:
        return CONFIG.copy()

    update_package = {}

    for valid_key in __VALID_KEYS__:
        if valid_key in new_config and new_config[valid_key] is not None:
            update_package[valid_key] = new_config[valid_key]

    __lock__.acquire()
    CONFIG.update(update_package)
    config_copy = CONFIG.copy()
    __lock__.release()

    __write_user_configuration__(config_copy)

    return config_copy


def __get_number_config_value__(
    config_key: str,
    default: float = 0
) -> float:
    """
    Get a configuration value from the config that is a boolean.
    If the value is not in the config, then use the default.

    Arguments:
        config_key {str} -- The name of the setting.
        default {float} -- The default value if the setting is not found.

    Returns:
        bool -- The value to use for the configuration.
    """
    try:
        is_config_ok = CONFIG is not None
        is_in_config = is_config_ok and config_key in CONFIG

        if is_in_config:
            return float(CONFIG[config_key])
    except Exception:
        return default

    return default


def __get_boolean_config_value__(
    config_key: str,
    default: bool = False
) -> bool:
    """
    Get a configuration value from the config that is a boolean.
    If the value is not in the config, then use the default.

    Arguments:
        config_key {str} -- The name of the setting.
        default {bool} -- The default value if the setting is not found.

    Returns:
        bool -- The value to use for the configuration.
    """
    try:
        if CONFIG is not None and config_key in CONFIG:
            return CONFIG[config_key]
    except Exception:
        return default

    return default


def get_mode():
    """
    Returns the mode given in the config.
    """

    return CONFIG['mode']


def get_visualizer_index(
    visualizers: list = None
) -> int:
    """
    Returns the index of the visualizer we will use.
    Performs basic clamping on the index if a list is provided.

    Returns:
        int: The index of the visualizer to use.
    """
    visualizer_index = int(
        __get_number_config_value__(VISUALIZER_INDEX_KEY, 0))

    if visualizers is None:
        return visualizer_index

    num_visualizers = len(visualizers)

    if visualizer_index < 0:
        visualizer_index = num_visualizers - 1

    if visualizer_index >= num_visualizers:
        visualizer_index = 0

    CONFIG[VISUALIZER_INDEX_KEY] = visualizer_index

    return visualizer_index


def update_visualizer_index(
    visualizers: list,
    new_index: int
) -> int:
    __lock__.acquire()
    CONFIG[VISUALIZER_INDEX_KEY] = new_index
    wrapped_index = get_visualizer_index(visualizers)
    __lock__.release()

    return wrapped_index


def get_pixel_order():
    """
    Get the pixel color order for WS281x/NeoPixel lights.
    If the value is not in the configuration, then the default is returned.

    Returns:
        str: The pixel color order descriptor.
    """
    try:
        value = CONFIG[PIXEL_ORDER_KEY]

        if value not in __VALID_PIXEL_ORDERS__:
            return PIXEL_ORDER_DEFAULT

        return value
    except Exception:
        return PIXEL_ORDER_DEFAULT


def get_blink_station_if_old_data() -> bool:
    """
    Should old stations blink if the data is considered too old?

    Returns:
        bool -- Should the station be blinked if the data is too old?
    """

    return __get_boolean_config_value__('blink_old_stations', True)


def get_metar_station_inactive_minutes() -> int:
    """
    How old can a METAR be and the station is still considered "Active"

    Returns:
        int: The number of minutes after which the station is considered inactive.
    """
    return __get_number_config_value__(METAR_STATION_INACTIVE_MINUTES_KEY, DEFAULT_METAR_STATION_INACTIVE_MINUTES)


def get_snow_pulse():
    """
    Do stations with snow in the precipitation pulse?
    """
    return __get_boolean_config_value__(SNOW_PULSE_KEY, False)


def get_snow_twinkle():
    """
    Do stations with snow in the precipitation view twinkle?
    """
    return __get_boolean_config_value__(SNOW_TWINKLE_KEY, True)

def get_lightning_blink():
    """
    Do statioins blink yellow when there is lightning reported?
    Flight rules visualizer only.
    """
    return __get_boolean_config_value__(LIGHTNING_BLINK_KEY, True)

def get_night_lights():
    """
    Should we light airports that are in Night differently?

    Returns:
        boolean -- True if we should light airports that are in the dark
        differently.
    """
    return __get_boolean_config_value__('night_lights')


def get_night_populated_yellow():
    """
    If we are using the option feature that shows day/night cycles,
    then should we use "populated yellow" as the target color?
    Defaults to True if the option is not in the config file.

    Returns:
        boolean -- True if the color of the station should be yellow when it is dark.
    """
    return __get_boolean_config_value__('night_populated_yellow', True)


def get_night_category_proportion():
    """
    If we are using the category color for the night conditions,
    then what proportion between the category and black should we use?
    0.0 is black. 1.0 is the normal category color.

    Returns:
        float -- A number between 0.0 (off) and 1.0 (true category color), inclusive
    """

    default_mix = 0.5

    try:
        unclamped = __get_number_config_value__(
            NIGHT_CATEGORY_PROPORTION_KEY,
            default_mix)

        if unclamped < 0.0:
            return 0.0

        if unclamped > 1.0:
            return 1.0

        return unclamped
    except Exception:
        return default_mix


def get_airport_configuration_section():
    """
    Returns the proper section of the configuration file
    to load the airport configuration from.

    Returns:
        string -- The key in the configuration JSON to
        load the airport configuration from.
    """

    return get_mode()


def get_brightness_proportion() -> float:
    """
    Get how much we want to adjust the brightness of the LEDs

    Returns:
        float -- The amount that the final color will be multiplied by
    """
    default = 1.0
    try:
        return __get_number_config_value__('brightness_proportion', default)
    except Exception:
        return default


def get_airport_file():
    """
    Returns the file that contains the airport config
    """

    return CONFIG['airports_file']


def get_airport_configs():
    """
    Returns the configuration for the lighting type

    Returns:
        dictionary -- Airport identifier keying lighting configuration.
    """

    return __load_station_config__(get_airport_file())


def __load_station_config__(
    config_file: str
) -> dict:
    """
    Loads the configuration for WS2801/neopixel based setups.

    Arguments:
        config_file {string} -- The file name & location to load.

    Returns:
        dict -- A dictionary keyed by airport identifier that holds the pixel index and a reserved value.
    """

    out_airport_map = {}

    json_config = __load_config_file__(config_file)
    stations = json_config[WS2801]

    for airport_data in stations:
        keylist = []
        keylist.extend(iter(airport_data.keys()))
        airport_code = keylist[0]
        normalized_code = airport_code.upper()

        if normalized_code not in out_airport_map:
            out_airport_map[normalized_code] = []

        out_airport_map[normalized_code].append(
            airport_data[airport_code]['neopixel'])

    return out_airport_map
