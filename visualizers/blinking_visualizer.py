import time
from datetime import datetime, timezone

from lib import safe_logging
from renderers.debug import Renderer
from visualizers.visualizer import Visualizer


class BlinkingVisualizer(Visualizer):
    def __init__(self, renderer: Renderer, stations: dict):
        super().__init__(renderer, stations)

    def render_station(self, station: str, is_blink: bool = False):
        """
        Sets the LED for a station.
        This is a default, empty, implementation meant to be overridden
        and simply define the interface.

        Args:
            renderer (Renderer): [description]
            airport (str): [description]
            is_blink (bool, optional): [description]. Defaults to False.
        """
        pass

    def render_station_displays(self, is_blink: bool) -> float:
        """
        Sets the LEDs for all of the airports based on their flight rules.
        Does this independent of the LED type.

        Arguments:
            is_blink {bool} -- Is this on the "off" cycle of blinking.
        """

        start_time = datetime.now(timezone.utc)

        for station in self.__stations__:
            try:
                self.render_station(station, is_blink)
            except Exception as ex:
                safe_logging.safe_log_warning(
                    f"Catch-all error in render_station_displays of {station} EX={ex}"
                )

        self.__renderer__.show()

        return (datetime.now(timezone.utc) - start_time).total_seconds()

    def update(self, time_slice: float):
        for is_blink in [True, False]:
            render_time = self.render_station_displays(is_blink)

            time_to_sleep = self.__get_update_interval__() - render_time

            if time_to_sleep > 0.0:
                time.sleep(time_to_sleep)

    def __get_update_interval__(self) -> float:
        return 1.0
