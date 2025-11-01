from datetime import datetime, timezone

from configuration import configuration
from lib import colors as colors_lib
from renderers.debug import Renderer
from visualizers.visualizer import Visualizer


class HalloweenLights(Visualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        orange = [240, 173, 31]
        green = [0, 255, 0]
        purple = [160, 32, 240]
        self.__colors__ = [orange, green, purple]
        self.__speed_adjustment__ = 2 # The higher the adjustment, the slower the lights. 2 is half the speed. 4 is quarter
        super().__init__(renderer, stations)

    def update(self, time_slice: float):
        current_seconds = datetime.now(timezone.utc).second * self.__speed_adjustment__
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]
        brightness_adjustment = configuration.get_brightness_proportion()
        brightness_adjusted_colors = [colors_lib.get_brightness_adjusted_color(color, brightness_adjustment)  for color in self.__colors__]
        color_count = len(brightness_adjusted_colors)

        mod_second = current_seconds % color_count

        for i in range(pixel_count):
            color_index = (i + mod_second)
            color_index = color_index if color_index < color_count else color_index - color_count
            color = brightness_adjusted_colors[color_index]

            self.__renderer__.set_led(i, color)

        self.__renderer__.show()
