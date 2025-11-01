from datetime import datetime, timezone

from configuration import configuration
from lib import colors as colors_lib
from renderers.debug import Renderer
from visualizers.visualizer import Visualizer


class HalloweenLights(Visualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        self.__orange__ = [255, 165, 0]
        self.__green__ = [0, 255, 0]
        self.__purple__ = [128, 0, 128]
        super().__init__(renderer, stations)

    def update(self, time_slice: float):
        current_seconds = datetime.now(timezone.utc).second
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]  # 1
        brightness_adjustment = configuration.get_brightness_proportion()
        orange = colors_lib.get_brightness_adjusted_color(
            self.__orange__, brightness_adjustment
        )
        green = colors_lib.get_brightness_adjusted_color(
            self.__green__, brightness_adjustment
        )
        purple = colors_lib.get_brightness_adjusted_color(
            self.__purple__, brightness_adjustment
        )

        colors = [orange, green, purple]

        for i in range(pixel_count):
            mod_second = current_seconds % 3
            color_index = (i + mod_second) % 3
            color = colors[color_index]

            self.__renderer__.set_led(i, color)

        self.__renderer__.show()
