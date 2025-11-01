from configuration import configuration
from lib import colors as colors_lib
from renderers.debug import Renderer
from visualizers.visualizer import Visualizer

from visualizers.rainbow_visualizer import wheel


class PongVisualizer(Visualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        self.__ball_color__ = [255, 255, 255]
        self.__trail_color__ = [240, 173, 31] # Orange
        self.__off__ = [0, 0, 0]
        # The lower the adjustment, the slower the lights. 0.5 is half the speed.
        # The higher the adjustment, the faster the lights. 2 is twice the speed.
        self.__speed_adjustment__ = 16
        self.__incremental_index__: float = 0
        self.__direction__:int = 1
        super().__init__(renderer, stations)

    def update(self, time_slice: float):
        elapsed_seconds:float = time_slice * self.__speed_adjustment__
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]
        brightness_adjustment = configuration.get_brightness_proportion()

        self.__incremental_index__ += (self.__direction__ * elapsed_seconds)
        index = int(self.__incremental_index__)

        if (index >= pixel_count):
            index = pixel_count - 1
            self.__incremental_index__ = index
            self.__direction__ = -1
        elif (index < 0):
            index = 0
            self.__incremental_index__ = 0
            self.__direction__ = 1

        self.__renderer__.set_all(self.__off__)

        brightness_adjusted_color = colors_lib.get_brightness_adjusted_color(self.__ball_color__, brightness_adjustment)
        self.__renderer__.set_led(index, brightness_adjusted_color)

        self.__renderer__.set_led(index - self.__direction__, colors_lib.get_brightness_adjusted_color(self.__trail_color__, brightness_adjustment / 2))
        self.__renderer__.set_led(index - (2 * self.__direction__), colors_lib.get_brightness_adjusted_color(self.__trail_color__, brightness_adjustment / 4))
        self.__renderer__.set_led(index - (3 * self.__direction__), colors_lib.get_brightness_adjusted_color(self.__trail_color__, brightness_adjustment / 8))

        self.__renderer__.show()
