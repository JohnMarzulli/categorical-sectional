import threading
from datetime import datetime, timezone, timedelta


class CacheEntry:
    def __init__(self, value, max_age_in_minutes: int):
        self.__expiration__ = datetime.now(timezone.utc) + timedelta(
            minutes=max_age_in_minutes
        )
        self.value = value

    def is_set(self) -> bool:
        return self.value is not None

    def is_valid(self) -> bool:
        return datetime.now(timezone.utc) < self.__expiration__


class CacheResult:
    def __init__(self, is_valid: bool, value):
        self.is_valid: bool = is_valid
        self.value = value if is_valid else None


class Cache:
    def __init__(self, max_cache_life_minutes: int = 8):
        self.__cache_lock__: threading.Lock = threading.Lock()
        self.__cache__: dict[str, CacheEntry] = {}
        self.__max_cache_life_minutes__: int = max_cache_life_minutes

    def set(self, station_icao_code: str, value):
        """
        Sets the given cache to have the given value.
        Automatically sets the cache saved time.

        Arguments:
            airport_icao_code {str} -- The code of the station to cache the results for.
            cache {dictionary} -- The cache keyed by airport code.
            value {object} -- The value to store in the cache.
        """

        self.__cache_lock__.acquire()
        try:
            self.__cache__[station_icao_code] = CacheEntry(
                value, self.__max_cache_life_minutes__
            )
        finally:
            self.__cache_lock__.release()

    def get_or_set(self, station: str, function) -> CacheResult:
        result = self.get(station)

        if not result.is_valid:
            new_value = function()

            if new_value is not None:
                self.set(station, new_value)

            return self.get(station)

        return result

    def get(self, station_icao_code: str) -> CacheResult:
        """
        Returns TRUE and the cached value if the cached value
        can still be used.

        Arguments:
            airport_icao_code {str} -- The airport code to get from the cache.
            cache {dictionary} -- Tuple of last update time and value keyed by airport code.
            cache_life_in_minutes {int} -- How many minutes until the cached value expires

        Returns:
            [type] -- [description]
        """

        self.__cache_lock__.acquire()

        now = datetime.now(timezone.utc)

        try:
            if station_icao_code in self.__cache__:
                return CacheResult(
                    self.__cache__[station_icao_code].is_valid(),
                    self.__cache__[station_icao_code].value,
                )
        except Exception:
            pass
        finally:
            self.__cache_lock__.release()

        return CacheResult(False, None)
