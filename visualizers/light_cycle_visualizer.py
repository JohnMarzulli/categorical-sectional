from configuration import configuration
from renderers.debug import Renderer
from visualizers.rainbow_visualizer import wheel
from visualizers.visualizer import Visualizer


class LightCycleVisualizer(Visualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        super().__init__(renderer, stations)

    def update(self, time_slice: float):
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]  # 1

        for j in range(255):  # one cycle of all 256 colors in the wheel
            pixel_index = (256 // pixel_count) + j
            # tricky math! we use each pixel as a fraction of the full 96-color wheel
            # (thats the i / strip.numPixels() part)
            # Then add in j which makes the colors go around per pixel
            # the % 96 is to make the wheel cycle around
            color = wheel(pixel_index & 255)

            self.__renderer__.set_all(color)
