from datetime import datetime, timezone

from configuration import configuration
from lib import colors as colors_lib
from renderers.debug import Renderer
from visualizers.visualizer import Visualizer


class HalloweenLightsVisualizer(Visualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        off = [0, 0, 0]
        orange = [240, 173, 31]
        green = [0, 255, 0]
        purple = [160, 32, 240]
        self.__colors__ = [off, off, orange, green, purple, off, off]
        # The lower the adjustment, the slower the lights. 0.5 is half the speed.
        # The higher the adjustment, the faster the lights. 2 is twice the speed.
        self.__speed_adjustment__ = 8
        self.__incremental_index__: float = 0.0
        super().__init__(renderer, stations)

    def update(self, time_slice: float):
        elapsed_seconds = time_slice * self.__speed_adjustment__
        self.__incremental_index__ += elapsed_seconds
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]
        brightness_adjustment = configuration.get_brightness_proportion()

        if self.__incremental_index__ > 1.0:
            self.__incremental_index__ -= 1.0
            new_color_order = [self.__colors__[-1]]
            new_color_order.extend(self.__colors__[:-1])
            self.__colors__ = new_color_order

        brightness_adjusted_colors: list = [colors_lib.get_brightness_adjusted_color(color, brightness_adjustment) for color in self.__colors__]
        color_count: int = len(brightness_adjusted_colors)
        color_index:int = 0

        for i in range(pixel_count):
            try:
                color_index = i % color_count
                color = brightness_adjusted_colors[color_index]

                self.__renderer__.set_led(i, color)
            except Exception as ex:
                print(f'While attempting to set LED:{i} with self.__incremental_index__:{self.__incremental_index__} to color_index:{color_index}. color_count:{color_count} EX={ex}')

        self.__renderer__.show()
