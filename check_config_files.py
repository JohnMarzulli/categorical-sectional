# Self-Test file that makes sure all
# off the station identifiers are OK.

import time

from configuration import configuration
from data_sources import weather
from lib import safe_logging


def terminal_error(
    error_message
):
    safe_logging.safe_log_warning(error_message)
    exit(0)


try:
    airport_render_config = configuration.get_airport_configs()
except Exception as e:
    terminal_error(
        'Unable to fetch the airport configuration. Please check the JSON files. Error={}'.format(e))

if len(airport_render_config) == 0:
    terminal_error('No airports found in the configuration file.')

stations_unable_to_fetch_weather = []

for station_id in airport_render_config:
    safe_logging.safe_log('Checking configuration for {}'.format(station_id))

    led_indices = airport_render_config[station_id]

    # Validate the index for the LED is within bounds
    for led_index in led_indices:
        if led_index < 0:
            terminal_error(
                'Found {} has an LED at a negative position {}'.format(
                    station_id,
                    led_index))

    # Validate that the station is in the CSV file
    try:
        data_file_icao_code = weather.get_faa_csv_identifier(station_id)
    except Exception as e:
        terminal_error(
            'Unable to fetch the station {} from the CSV data file. Please check that the station is in the CSV file. Error={}'.format(station_id, e))

    if data_file_icao_code is None or data_file_icao_code == '' or weather.INVALID in data_file_icao_code:
        terminal_error(
            'Unable to fetch the station {} from the CSV data file. Please check that the station is in the CSV file. Error={}'.format(
                station_id))

    # Validate that the station can have weather fetched
    metar = weather.get_metar(station_id)

    if metar is None or weather.INVALID in metar:
        stations_unable_to_fetch_weather.append(station_id)
        safe_logging.safe_log_warning(
            'Unable to fetch weather for {}/{}'.format(
                station_id,
                led_indices))

    # Validate that the station can have Sunrise/Sunset fetched
    day_night_info = weather.get_civil_twilight(station_id)

    if day_night_info is None:
        terminal_error(
            'Unable to fetch day/night info for {}/{}'.format(
                station_id,
                led_indices))

    if len(day_night_info) != 6:
        terminal_error(
            'Unknown issue fetching day/night info for {}/{}'.format(
                station_id,
                led_indices))

safe_logging.safe_log('')
safe_logging.safe_log('')
safe_logging.safe_log('-------------------------')
safe_logging.safe_log(
    'Finished testing configuration files. No fatal issues were found.')
safe_logging.safe_log('')
safe_logging.safe_log(
    'Unable to fetch the weather for the following stations:')

for station in stations_unable_to_fetch_weather:
    safe_logging.safe_log('\t {}'.format(station))

safe_logging.safe_log(
    'Please check the station identifier. The station may be out of service, temporarily down, or may not exist.')
