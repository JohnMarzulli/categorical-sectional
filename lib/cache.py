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
        self.__cache__: dict = {}
        self.__max_cache_life_minutes__: int = max_cache_life_minutes

    def set(self, key: str, value):
        """
        Sets the given cache to have the given value.
        Automatically sets the cache saved time.

        Arguments:
            key {str} -- The key of the cache entry.
            value {object} -- The value to store in the cache.
        """

        self.__cache_lock__.acquire()
        try:
            self.__cache__[key] = CacheEntry(
                value, self.__max_cache_life_minutes__
            )
        finally:
            self.__cache_lock__.release()

    def get_or_set(self, key: str, function) -> CacheResult:
        result = self.get(key)

        if not result.is_valid:
            new_value = function()

            if new_value is not None:
                self.set(key, new_value)

            return self.get(key)

        return result

    def get(self, key: str) -> CacheResult:
        """
        Returns a CacheResult for the given key in the cache

        Arguments:
            key {str} -- The name of the item in the cache

        Returns:
            CacheResult -- The item (and a validity flag) from the cache.
        """

        self.__cache_lock__.acquire()

        try:
            if key in self.__cache__:
                return CacheResult(
                    self.__cache__[key].is_valid(),
                    self.__cache__[key].value,
                )
        except Exception:
            pass
        finally:
            self.__cache_lock__.release()

        return CacheResult(False, None)
