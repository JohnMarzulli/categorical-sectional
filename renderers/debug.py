"""
Simple driver of the WS281x addressable RGB LED lights, commonly called "NeoPixels"
Based on the AdaFruit example.
License: Public Domain
"""

from __future__ import division


class Renderer(object):
    def __init__(self, pixel_count):
        """
        Create a "renderer" for debugging.

        Arguments:
            pixel_count {int} -- The total number of neopixels.
        """

        super().__init__()

        self.pixel_count: int = pixel_count
        self.pixels: list[tuple] = [(0, 0, 0)] * pixel_count
        self.__is_dirty__: bool = False

    def set_all(self, color: tuple):
        """
        Sets all of the LEDs to the same color.

        Args:
            color (list): The color we want to set all of the LEDs to.
        """
        self.pixels = [color] * self.pixel_count
        self.show()

    def set_led(self, pixel_index: int, color: tuple):
        """
        Sets the given airport to the given color

        Arguments:
            pixel_index {int} -- The index of the pixel to set
            color {int array} -- The RGB (0-255) array of the color we want to set.
        """
        if pixel_index >= self.pixel_count:
            return

        if pixel_index < 0:
            return

        self.pixels[pixel_index] = color
        self.__is_dirty__ = True

    def set_leds(self, pixel_list: list, color: tuple):
        """
        Sets all of the pixels in the given list to the given color.

        Args:
            pixel_list (list): A list of pixel indices to set.
            color (list): The color to set the pixels to.
        """
        for pixel_index in pixel_list:
            self.set_led(pixel_index, color)

    def show(self):
        self.__is_dirty__ = False

    def clear(self):
        self.set_all((0, 0, 0))
