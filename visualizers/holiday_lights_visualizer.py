from datetime import datetime, timezone

from configuration import configuration
from lib import colors as colors_lib
from renderers.debug import Renderer
from visualizers.visualizer import Visualizer


class HolidayLights(Visualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        self.__red__ = [255, 0, 0]
        self.__green__ = [0, 255, 0]
        super().__init__(renderer, stations)

    def update(self, time_slice: float):
        current_seconds = datetime.now(timezone.utc).second
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]  # 1
        brightness_adjustment = configuration.get_brightness_proportion()
        red = colors_lib.get_brightness_adjusted_color(
            self.__red__, brightness_adjustment
        )
        green = colors_lib.get_brightness_adjusted_color(
            self.__green__, brightness_adjustment
        )

        for i in range(pixel_count):
            is_even_second = (current_seconds % 2) is 0
            is_even_pixel = (i % 2) is 0
            color = self.__green__

            if is_even_pixel:
                color = red if is_even_second else green
            else:
                color = green if is_even_second else red

            self.__renderer__.set_led(i, color)

        self.__renderer__.show()
