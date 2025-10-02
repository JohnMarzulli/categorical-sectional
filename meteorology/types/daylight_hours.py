from datetime import datetime


class DaylightHours:
    # 0 - When sunrise starts
    # 1 - when sunrise is
    # 2 - when full light starts
    # 3 - when full light ends
    # 4 - when sunset starts
    # 5 - when it is full dark

    def __init__(
        self,
        sunrise_start: datetime,
        sunrise: datetime,
        full_light_start: datetime,
        full_light_end: datetime,
        sunset: datetime,
        sunset_end: datetime,
    ):
        self.sunrise_start = sunrise_start  # 0
        self.sunrise = sunrise  # 1
        self.full_light_start = full_light_start  # 2
        self.full_light_end = full_light_end  # 3
        self.sunset = sunset  # 4
        self.sunset_end = sunset_end  # 5
