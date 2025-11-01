from renderers.debug import Renderer
from visualizers.flight_rules_visualizer import FlightRulesVisualizer
from visualizers.pressure_visualizer import PressureVisualizer
from visualizers.rainbow_visualizer import RainbowVisualizer
from visualizers.halloween_lights_visualizer import HalloweenLightsVisualizer
from visualizers.pong_visualizer import PongVisualizer
from visualizers.holiday_lights_visualizer import HolidayLights
from visualizers.light_cycle_visualizer import LightCycleVisualizer
from visualizers.precipitation_visualizer import PrecipitationVisualizer
from visualizers.temperature_visualizer import TemperatureVisualizer


class VisualizerManager(object):
    __VISUALIZERS__: list = []

    @staticmethod
    def get_visualizers() -> list:
        return VisualizerManager.__VISUALIZERS__

    @staticmethod
    def initialize_visualizers(renderer: Renderer, stations: dict) -> list:
        if len(VisualizerManager.__VISUALIZERS__) > 0:
            return VisualizerManager.__VISUALIZERS__

        VisualizerManager.__VISUALIZERS__ = [
            FlightRulesVisualizer(renderer, stations),
            TemperatureVisualizer(renderer, stations),
            PrecipitationVisualizer(renderer, stations),
            PressureVisualizer(renderer, stations),
            RainbowVisualizer(renderer, stations),
            LightCycleVisualizer(renderer, stations),
            HolidayLights(renderer, stations),
            HalloweenLightsVisualizer(renderer, stations),
            PongVisualizer(renderer, stations),
        ]

        return VisualizerManager.__VISUALIZERS__
