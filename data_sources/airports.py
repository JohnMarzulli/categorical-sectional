import csv
import os

from meteorology.types.location import Location

__default_working_directory__: str = os.path.dirname(os.path.abspath(__file__))


def __load_airport_data__(
    working_directory=__default_working_directory__,
    airport_data_file="../data/us-airports.csv",
):
    """
    Loads all of the airport and weather station data from the included CSV file
    then places it into a dictionary for easy use.

    The data can be updated from https://ourairports.com/countries/US/airports.csv

    Keyword Arguments:
        airport_data_file {str} -- The file that contains the airports (default: {"../data/us-airports.csv"})

    Returns:
        dictionary -- A map of the airport data keyed by ICAO code.
    """
    full_file_path = os.path.join(
        working_directory, os.path.normpath(airport_data_file)
    )

    csv_file = open(full_file_path, "r", encoding="utf-8")

    fieldnames = (
        "id",
        "ident",
        "type",
        "name",
        "latitude_deg",
        "longitude_deg",
        "elevation_ft",
        "continent",
        "iso_country",
        "iso_region",
        "municipality",
        "scheduled_service",
        "gps_code",
        "iata_code",
        "local_code",
        "home_link",
        "wikipedia_link",
        "keywords",
    )
    reader = csv.DictReader(csv_file, fieldnames)

    return {
        row["ident"]: {
            "lat": row["latitude_deg"],
            "long": row["longitude_deg"],
        }
        for row in reader
    }


def get_faa_csv_identifier(station_icao_code: str):
    """
    Checks to see if the given identifier is in the FAA CSV file.
    If it is not, then checks to see if it is one of the airports
    that the weather service requires a "K" prefix, but the CSV
    file is without it.

    Returns any identifier that is in the CSV file.
    Returns None if the airport is not in the file.

    Arguments:
        airport_icao_code {string} -- The full identifier of the airport.
    """

    if station_icao_code is None:
        return None

    normalized_icao_code = station_icao_code.upper()

    if normalized_icao_code in __airport_locations__:
        return normalized_icao_code

    if len(normalized_icao_code) >= 4:
        normalized_icao_code = normalized_icao_code[-3:]

        if normalized_icao_code in __airport_locations__:
            return normalized_icao_code

    if len(normalized_icao_code) <= 3:
        normalized_icao_code = f"K{normalized_icao_code}"

        if normalized_icao_code in __airport_locations__:
            return normalized_icao_code

    return None


def get_location(station_code: str) -> Location:
    faa_code = get_faa_csv_identifier(station_code)

    if faa_code is None:
        return Location(0, 0)

    lat = float(str(__airport_locations__[faa_code]["lat"]))
    lon = float(str(__airport_locations__[faa_code]["long"]))

    return Location(lat, lon)


__airport_locations__ = __load_airport_data__()
