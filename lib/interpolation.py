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


def get_proportion_between_floats(start: float, current: float, end: float):
    """
    Gets the "distance" (0.0 to 1.0) between the start and the end where the current is.
    Could be thought as the reverse of interpolation
    IE:
        If the Current is the same as Start, then the result will be 0.0
        If the Current is the same as the End, then the result will be 1.0
        If the Current is halfway between Start and End, then the result will be 0.5


    Arguments:
        start {float} -- The starting temp.
        current {float} -- The temp we want to get the proportion for.
        end {float} -- The end temp to calculate the interpolaton for.

    Returns:
        float -- The amount of interpolaton for Current between Start and End

        >>> get_proportion_between_floats(0.0, 0.0, 1.0)
        0.0
        >>> get_proportion_between_floats(0.0, 1.0, 1.0)
        1.0
        >>> get_proportion_between_floats(0.0, 0.5, 1.0)
        0.5
        >>> get_proportion_between_floats(0.0, 5.0, 10.0)
        0.5
        >>> get_proportion_between_floats(0.0, -1, 10.0)
        0.0
        >>> get_proportion_between_floats(0.0, 20, 10.0)
        1.0
    """

    current = clamp(start, current, end)

    total_delta = end - start
    time_in = current - start

    return time_in / total_delta


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
