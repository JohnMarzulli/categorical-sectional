from configuration import configuration
from renderers.debug import Renderer
from visualizers.visualizer import Visualizer


def wheel(pos) -> list:
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return [r, g, b]


class RainbowVisualizer(Visualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        super().__init__(renderer, stations)

    def update(self, time_slice: float):
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]  # 1

        for j in range(255):  # one cycle of all 256 colors in the wheel
            for i in range(pixel_count):
                pixel_index = (i * 256 // pixel_count) + j
                # tricky math! we use each pixel as a fraction of the full 96-color wheel
                # (thats the i / strip.numPixels() part)
                # Then add in j which makes the colors go around per pixel
                # the % 96 is to make the wheel cycle around
                color = wheel(pixel_index & 255)

                self.__renderer__.set_led(i, color)

            self.__renderer__.show()
