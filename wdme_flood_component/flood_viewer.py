import flood_thread
import json

class FloodViewer (flood_thread.ThreadedService):

    def __init__(self, datapath:str, logger=None):
        super().__init__(logger)

        with open(datapath, "r") as f:
            self.data = json.load(f)

    def get_flood_model(self, datapath:str) ->dict:
        return self.data['data'][datapath]

    def get_current_results(self) -> dict:
        return self.data['result']
