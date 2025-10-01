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
        RED: (255, 0, 0),
        LIGHT_RED: (255, 105, 180),
        GREEN: (0, 255, 0),
        BLUE: (0, 0, 255),
        LIGHT_BLUE: (51, 255, 255),
        MAGENTA: (255, 0, 255),
        OFF: (0, 0, 0),
        GRAY: (50, 50, 50),
        LIGHT_GRAY: (128, 128, 128),
        YELLOW: (255, 255, 0),
        DARK_YELLOW: (20, 20, 0),
        WHITE: (255, 255, 255),
        PURPLE: (148, 0, 211),
        ORANGE: (255, 126, 0),
    }


def clamp(minimum, value, maximum):
    """
    Makes sure the given value (middle param) is always between the maximum and minimum.

    Arguments:
        minimum {number} -- The smallest the value can be (inclusive).
        value {number} -- The value to clamp.
        maximum {number} -- The largest the value can be (inclusive).

    Returns:
        number -- The value within the allowable range.
    """

    return minimum if value < minimum else min(value, maximum)


def interpolate(left_value, right_value, proportion):
    """
    Finds the spot between the two values.

    Arguments:
        left_value {number} -- The value on the "left" that 0.0 would return.
        right_value {number} -- The value on the "right" that 1.0 would return.
        proportion {float} -- The proportion from the left to the right hand side.

    >>> interpolate(0, 255, 0.5)
    127
    >>> interpolate(10, 20, 0.5)
    15
    >>> interpolate(0, 255, 0.0)
    0
    >>> interpolate(0, 255, 0)
    0
    >>> interpolate(0, 255, 1)
    255
    >>> interpolate(0, 255, 1.5)
    255
    >>> interpolate(0, 255, -0.5)
    0
    >>> interpolate(0, 255, 0.1)
    25
    >>> interpolate(0, 255, 0.9)
    229
    >>> interpolate(255, 0, 0.5)
    127
    >>> interpolate(20, 10, 0.5)
    15
    >>> interpolate(255, 0, 0.0)
    255
    >>> interpolate(255, 0, 0)
    255
    >>> interpolate(255, 0, 1)
    0
    >>> interpolate(255, 0, 1.5)
    0
    >>> interpolate(255, 0, -0.5)
    255
    >>> interpolate(255, 0, 0.1)
    229
    >>> interpolate(255, 0, 0.9)
    25

    Returns:
        float -- The number that is the given amount between the left and right.
    """

    left_value = clamp(0.0, left_value, 255.0)
    right_value = clamp(0.0, right_value, 255.0)
    proportion = clamp(0.0, proportion, 1.0)

    return clamp(
        0,
        int(
            float(left_value)
            + (float(right_value - float(left_value)) * float(proportion))
        ),
        255,
    )


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
        int(interpolate(left_color[index], right_color[index], proportion))
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
