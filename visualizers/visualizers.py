import visualizers.halloween_lights_visualizer
import visualizers.holiday_lights_visualizer
import visualizers.light_cycle_visualizer
import visualizers.precipitation_visualizer
import visualizers.temperature_visualizer
from renderers.debug import Renderer
from visualizers import flight_rules_visualizer, pressure_visualizer, rainbow_visualizer


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
            flight_rules_visualizer.FlightRulesVisualizer(renderer, stations),
            visualizers.temperature_visualizer.TemperatureVisualizer(
                renderer, stations
            ),
            visualizers.precipitation_visualizer.PrecipitationVisualizer(
                renderer, stations
            ),
            pressure_visualizer.PressureVisualizer(renderer, stations),
            rainbow_visualizer.RainbowVisualizer(renderer, stations),
            visualizers.light_cycle_visualizer.LightCycleVisualizer(renderer, stations),
            visualizers.holiday_lights_visualizer.HolidayLights(renderer, stations),
            visualizers.halloween_lights_visualizer.HalloweenLights(renderer, stations),
        ]

        return VisualizerManager.__VISUALIZERS__
