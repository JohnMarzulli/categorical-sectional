def celsius_to_fahrenheit(temperature_celsius: float) -> float:
    """
    Convert a temperature in Celsius to Fahrenheit.

    Args:
        temperature_celsius (float | None): Temperature in °C. If None, returns 0.0.

    Returns:
        float: Temperature converted to °F.

    Examples:
        >>> celsius_to_fahrenheit(0.0)
        32.0
        >>> celsius_to_fahrenheit(100.0)
        212.0
        >>> celsius_to_fahrenheit(-40.0)
        -40.0
        >>> celsius_to_fahrenheit(None)
        0.0
    """
    if temperature_celsius is None:
        return 0.0
    return (temperature_celsius * (9.0 / 5.0)) + 32.0


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
