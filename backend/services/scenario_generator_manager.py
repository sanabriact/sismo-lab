from backend.services.station_generator import StationGenerator

class ScenarioGeneratorManager:
    def __init__(self, ai_client, engine):
        self.ai_client = ai_client
        self.engine = engine
        self.generators = []

    def load_scenario(self, observatory):
        self.stop_all()
        self.engine.set_observatory(observatory)

        for station in observatory.getStations():
            generator = StationGenerator(
                station,
                self.ai_client,
                self.engine,
            )

            generator.start()
            self.generators.append(generator)

    def stop_all(self):
        for generator in self.generators:
            generator.stop()

        self.generators = []