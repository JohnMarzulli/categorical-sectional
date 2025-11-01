if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import lib.interpolation as interpolation

RED = "RED"
LIGHT_RED = "LIGHT RED"
GREEN = "GREEN"
BLUE = "BLUE"
LIGHT_BLUE = "LIGHT BLUE"
GRAY = "GRAY"
LIGHT_GRAY = "LIGHT GRAY"
YELLOW = "YELLOW"
DARK_YELLOW = "DARK YELLOW"
WHITE = "WHITE"
MAGENTA = "MAGENTA"
PURPLE = "PURPLE"
ORANGE = "ORANGE"
OFF = "OFF"


def get_colors() -> dict:
    """
    Returns the RGB colors based on the config.
    """

    return {
        RED: [255, 0, 0],
        LIGHT_RED: [255, 105, 180],
        GREEN: [0, 255, 0],
        BLUE: [0, 0, 255],
        LIGHT_BLUE: [51, 255, 255],
        MAGENTA: [255, 0, 255],
        OFF: [0, 0, 0],
        GRAY: [50, 50, 50],
        LIGHT_GRAY: [128, 128, 128],
        YELLOW: [255, 255, 0],
        DARK_YELLOW: [20, 20, 0],
        WHITE: [255, 255, 255],
        PURPLE: [148, 0, 211],
        ORANGE: [255, 126, 0],
    }


def get_color_mix(left_color: list, right_color: list, proportion) -> list:
    """
    Returns a color that is a mix between the two given colors.
    A given proportion of 0 would return the left color.
    A given proportion of 1 would return the right_color.
    A given proportion of 0.5 would return a 50/50 mix.

    Works for RGB or ARGB, but both sides MUST have matching number of components.

    >>> get_color_mix([0,0,0], [255, 255, 255], 0.0)
    [0, 0, 0]

    >>> get_color_mix([0,0,0], [255, 255, 255], 1.0)
    [255, 255, 255]

    >>> get_color_mix([0,0,0], [255, 255, 255], 0.5)
    [127, 127, 127]

    >>> get_color_mix([125,255,0], [125, 0, 255], 0.5)
    [125, 127, 127]

    >>> get_color_mix([255, 255, 255], [0,0,0], 0.5)
    [127, 127, 127]

    >>> get_color_mix([125, 0, 255], [125,255,0], 0.5)
    [125, 127, 127]

    Arguments:
        left_color {float[]} -- The starting color.
        right_color {float[]} -- The ending color.
        proportion {float} -- The mix between the two colors.

    Returns:
        float[] -- The new color.
    """

    array_length = len(left_color)
    if array_length != len(right_color):
        return left_color

    indices = range(array_length)
    return [
        int(
            interpolation.interpolate(left_color[index], right_color[index], proportion)
        )
        for index in indices
    ]


def get_brightness_adjusted_color(
    color_to_render: list, brightness_adjustment: float
) -> list:
    brightness_adjustment = max(brightness_adjustment, 0.0)
    final_color = []

    for color in color_to_render:
        reduced_color = float(color) * brightness_adjustment

        # Some colors are floats, some are integers.
        # Make sure we keep everything the same.
        if isinstance(color, int):
            reduced_color = int(reduced_color)

        final_color.append(reduced_color)

    return final_color


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
