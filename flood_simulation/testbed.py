import os
import datetime

import unexecore.testharness
import unexecore.debug

import flood_simulation.rainfall_model
import flood_simulation.visualisation
import flood_simulation.wdme_results

import json
import unexecore.geofile

class etteln_Harness(unexecore.testharness.TestHarness):
    def __init__(self):
        super().__init__()

        self.output_filepath = os.getcwd() + os.sep + 'output' + os.sep
        self.model = flood_simulation.rainfall_model.Model(output_filepath=self.output_filepath)

        option_id = 1

        self.options[str(option_id)] = {'label': 'std_model', 'function': self.std_model}
        option_id += 1


    def log(self, text):
        print(text)

    def std_model(self):
        data = [
          {
            "Last72Hour": 0,
            "Last24Hour": 0,
            "Last12Hour": 0,
            "Last4Hour": 0,
            "Last2Hour": 0,
            "LastHour": 0,
            "Forecast2Hour": 50,
            "Forecast0To24": 50,
            "Forecast24To48": 0,
            "Forecast48To72": 0,
            "TrafficLights": {
              "current": "green",
              "nowcast": "red",
              "forecast": "amber"
            },
            "dateObserved": "2025-09-04T02:00:00Z"
          }
        ]
        try:
            result = self.model.run(data[0], timestamp=datetime.datetime.now(datetime.timezone.utc))
            wdme_results = flood_simulation.wdme_results.create_results(result,'http://whatever.com')
            print(json.dumps(wdme_results, indent=4))

        except Exception as e:
            self.log(unexecore.debug.exception_to_string(e))

if __name__ == '__main__':
    harness = etteln_Harness()
    harness.run()