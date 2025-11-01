# Self-Test file that makes sure all
# off the station identifiers are OK.

from configuration import configuration
from data_sources import weather
from data_sources.airports import get_faa_csv_identifier
from data_sources.daylight import get_civil_twilight
from lib import safe_logging
from meteorology.types.classifications import INVALID
from meteorology.types.daylight_hours import DaylightHours
from meteorology.types.metar import Metar


def terminal_error(error_message):
    safe_logging.safe_log_warning(error_message)
    exit(0)


try:
    airport_render_config = configuration.get_airport_configs()
except Exception as e:
    terminal_error(
        f"Unable to fetch the airport configuration. Please check the JSON files. Error={e}"
    )

if len(airport_render_config) == 0:
    terminal_error("No airports found in the configuration file.")

stations_unable_to_fetch_weather = []

for station_id in airport_render_config:
    safe_logging.safe_log(f"Checking configuration for {station_id}")

    led_indices = airport_render_config[station_id]

    # Validate the index for the LED is within bounds
    for led_index in led_indices:
        if led_index < 0:
            terminal_error(
                f"Found {station_id} has an LED at a negative position {led_index}"
            )

    # Validate that the station is in the CSV file
    try:
        data_file_icao_code = get_faa_csv_identifier(station_id)
    except Exception as e:
        terminal_error(
            f"Unable to fetch the station {station_id} from the CSV data file. Please check that the station is in the CSV file. Error={e}"
        )

    if (
        data_file_icao_code is None
        or data_file_icao_code == ""
        or INVALID in data_file_icao_code
    ):
        terminal_error(
            f"Unable to fetch the station {station_id} from the CSV data file. Please check that the station is in the CSV file. Error=None"
        )

    # Validate that the station can have weather fetched
    metar: Metar = weather.get_metar(station_id)

    if metar is None or not metar.is_valid():
        stations_unable_to_fetch_weather.append(station_id)
        safe_logging.safe_log_warning(
            f"Unable to fetch weather for {station_id}/{led_indices}"
        )

    # Validate that the station can have Sunrise/Sunset fetched
    day_night_info: DaylightHours = get_civil_twilight(station_id)

    if day_night_info is None:
        terminal_error(f"Unable to fetch day/night info for {station_id}/{led_indices}")

safe_logging.safe_log("")
safe_logging.safe_log("")
safe_logging.safe_log("-------------------------")
safe_logging.safe_log(
    "Finished testing configuration files. No fatal issues were found."
)
safe_logging.safe_log("")
safe_logging.safe_log("Unable to fetch the weather for the following stations:")

for station in stations_unable_to_fetch_weather:
    safe_logging.safe_log(f"\t {station}")

safe_logging.safe_log(
    "Please check the station identifier. The station may be out of service, temporarily down, or may not exist."
)
