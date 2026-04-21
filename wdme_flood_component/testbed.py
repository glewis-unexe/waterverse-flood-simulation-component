import os
import datetime
import inspect

import unexecore.testharness
import unexecore.debug
import unexecore.logger
import unexecore.time

import flood_simulation.rainfall_model
import flood_simulation.wdme_results

import json

from pip._internal.commands import inspect


class EttelnModel(flood_simulation.rainfall_model.Model):
    def __init__(self, output_filepath:str):
        super().__init__(output_filepath)

        self.dem_model = 'etteln_demv5.asc'
        self.land_mask = 'etteln_land_maskv5.asc'
        self.rain_mask = 'etteln_rain_maskv5.asc'
        self.infiltration = 'infiltrationRates.csv'
        self.roughness = 'roughnessRates.csv'

        self.location_src_root = os.getcwd() + os.sep + 'locations/etteln/'

    def setup_rainfall_scenario_data(self, result:dict):
        scenario_data = {}

        self.current_scenario = {}
        self.nowcast_scenario = {}
        self.forecast_scenario = {}

        try:
            if 'data' in result:
                scenario_data = self.HST_to_sensible(result['data'])

        except Exception as e:
            pass

        if scenario_data == {}:
            try:
                if 'sensors' in result:
                    scenario_data = self.HST_to_sensible(result['sensors'])

            except Exception as e:
                pass

        if scenario_data == {}:
            try:
                if 'sensors' in result:
                    if isinstance(result['sensors'], dict):
                        result = result['sensors']
                    else:
                        result = result['sensors'][-1]

                scenario_data = {
                    '2169': result,
                    '2172': result,
                    '2173': result,
                    '2174': result,
                    '2175': result
                }

            except Exception as e:
                pass

        try:
            for sensor in scenario_data:
                self.current_scenario[sensor] = self.HST_hist_to_timeseries(scenario_data[sensor])
                self.nowcast_scenario[sensor] = self.HST_nowcast_to_timeseries(scenario_data[sensor])
                self.forecast_scenario[sensor] = self.HST_forecast_to_timeseries(scenario_data[sensor])
        except Exception as e:
                self.log(unexecore.debug.exception_to_string(e))
                return False

        return True

    def HST_hist_to_timeseries(self, data: dict) -> dict:

        if 'Last72Hour' not in data:
            print()

        last_2_days = data['Last72Hour'] - data['Last24Hour']
        last_day = data['Last24Hour'] - data['Last12Hour']
        last_12 = data['Last12Hour'] - data['Last4Hour']
        last_4 = data['Last4Hour'] - data['Last2Hour']
        last_2 = data['Last2Hour'] - data['LastHour']
        last_1 = data['LastHour']

        timeseries = []
        timeseries.append(0)

        index = 1
        for i in range(0, 48):
            timeseries.append(round(last_2_days / 48, 2))

        for i in range(0, 12):
            timeseries.append(round(last_day / 12, 2))

        for i in range(0, 8):
            timeseries.append(round(last_12 / 8, 2))
            index += 1

        for i in range(0, 2):
            timeseries.append(round(last_4 / 2, 2))
            index += 1

        timeseries.append(round(last_2, 2))
        timeseries.append(round(last_1, 2))

        return timeseries

    def HST_nowcast_to_timeseries(self, data: dict) -> dict:
        """
            nowcast is 2hrs
        :param data:
        :return:
        """
        timeseries = []
        timeseries.append(0)
        timeseries.append(round(data['Forecast2Hour'] / 2, 2))
        timeseries.append(round(data['Forecast2Hour'] / 2, 2))

        return timeseries

    def HST_forecast_to_timeseries(self, data: dict) -> dict:
        """
        forecast is 3days - 2hrs
        "Forecast2Hour"
        "Forecast0To24"
        "Forecast24To48"
        "Forecast48To72"
        """
        timeseries = []
        timeseries.append(0)

        for i in range(0, 22):
            timeseries.append(round((data['Forecast0To24'] - data['Forecast2Hour']) / 24, 2))

        for i in range(0, 24):
            timeseries.append(round(data['Forecast24To48'] / 24, 2))

        for i in range(0, 24):
            timeseries.append(round(data['Forecast48To72'] / 24, 2))

        return timeseries

    def HST_to_sensible(self, data) -> dict:
        rain_period_labels = [
            "Last72Hour",
            "Last24Hour",
            "Last12Hour",
            "Last4Hour",
            "Last2Hour",
            "LastHour",
            "Last5Minutes",

            "Forecast2Hour",
            "Forecast0To24",
            "Forecast24To48",
            "Forecast48To72",
        ]

        sensible_data = {}

        labels = []
        ids = []
        for entry in data:
            parts = entry['description'].split('.')

            # print(str(parts) + ' ' + str(round(entry['precipitation'],2)))

            if parts[1] not in labels:
                labels.append(parts[1])

            if parts[0] not in sensible_data:
                sensible_data[parts[0]] = {}

                for label in rain_period_labels:
                    sensible_data[parts[0]][label] = 0

            if parts[1] in sensible_data[parts[0]]:
                sensible_data[parts[0]][parts[1]] = round(entry['precipitation'], 2)

            if parts[0] not in ids:
                ids.append(parts[0])

        if False:
            for sensor_id in sensible_data:
                print(sensor_id)
                for period in sensible_data[sensor_id]:
                    print('\t' + str(period) + ' ' + str(sensible_data[sensor_id][period]))

        return sensible_data

class TorbayModel(EttelnModel):
    def __init__(self, output_filepath:str):
        super().__init__(output_filepath)

        self.land_mask = 'catchment_landcover_8m.asc'
        self.rain_mask = 'catchment_mask_8m.asc'
        self.dem_model = 'catchment_dem_8m.asc'

        self.roughness = 'roughnesses.csv'
        self.infiltration = 'infiltration.csv'

        self.location_src_root = os.getcwd() + os.sep + 'locations/torbay/'

    def setup_rainfall_scenario_data(self, result:dict):
        scenario_data = {}

        self.current_scenario = {}
        self.nowcast_scenario = {}
        self.forecast_scenario = {}

        try:
            if 'data' in result:
                scenario_data = self.HST_to_sensible(result['data'])

        except Exception as e:
            pass

        if scenario_data == {}:
            try:
                if 'sensors' in result:
                    scenario_data = self.HST_to_sensible(result['sensors'])

            except Exception as e:
                pass

        if scenario_data == {}:
            try:
                if 'sensors' in result:
                    if isinstance(result['sensors'], dict):
                        result = result['sensors']
                    else:
                        result = result['sensors'][-1]

                scenario_data = {
                    #'3': result, #3 is the mask
                    '1': result,
                }

            except Exception as e:
                pass

        try:
            for sensor in scenario_data:
                self.current_scenario[sensor] = self.HST_hist_to_timeseries(scenario_data[sensor])
                self.nowcast_scenario[sensor] = self.HST_nowcast_to_timeseries(scenario_data[sensor])
                self.forecast_scenario[sensor] = self.HST_forecast_to_timeseries(scenario_data[sensor])
        except Exception as e:
                unexecore.logger.logger.log(inspect.currentframe(),unexecore.debug.exception_to_string(e))
                return False

        return True


class simulation_Harness(unexecore.testharness.TestHarness):
    def __init__(self):
        super().__init__()

        option_id = 1


        # create the options for the test harness, using the scenarios from the ettlen attributes
        # do the core loop twice, firstly to build a set of options for generating results locally
        # and secondly to create the HTTP calls for the WDME flood component
        try:

            self.options[str(option_id)] = {'label': 'Etteln', 'function': self.etteln_model, 'args': {}}
            option_id += 1

            self.options[str(option_id)] = {'label': 'Torbay', 'function': self.torbay_model, 'args': {}}
            option_id += 1


        except Exception as e:
            unexecore.logger.logger.log(inspect.currentframe(),unexecore.debug.exception_to_string(e))



    def log(self, text):
        print(text)

    def torbay_model(self, args: dict):
        try:
            output_filepath = os.getcwd() + os.sep + 'sim_output/torbay/'
            model = TorbayModel(output_filepath=output_filepath)

            timestamp = datetime.datetime.now()

            data = {
                "Last72Hour": 100,
                "Last24Hour": 100,
                "Last12Hour": 100,
                "Last4Hour": 100,
                "Last2Hour": 100,
                "LastHour": 100,
                "Forecast2Hour": 100,
                "Forecast0To24": 100,
                "Forecast24To48": 100,
                "Forecast48To72": 100,
                "TrafficLights": {
                    "current": "test-1",
                    "nowcast": "test-2",
                    "forecast": "test-3"
                },
                "dateObserved": timestamp
            }
            result = model.run(data, timestamp= timestamp,asc_scale=100)

            wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:27700',  server_path='http://test.com', flip_coords=True)
            print()

            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)


        except Exception as e:
            unexecore.logger.logger.log(inspect.currentframe(), unexecore.debug.exception_to_string(e))

    def etteln_model(self, args:dict):
        try:
            output_filepath = os.getcwd() + os.sep + 'sim_output/etteln/'
            model = EttelnModel(output_filepath=output_filepath)

            timestamp = datetime.datetime.now()

            data = {
                "Last72Hour": 100,
                "Last24Hour": 100,
                "Last12Hour": 100,
                "Last4Hour": 100,
                "Last2Hour": 100,
                "LastHour": 100,
                "Forecast2Hour": 100,
                "Forecast0To24": 100,
                "Forecast24To48": 100,
                "Forecast48To72": 100,
                "TrafficLights": {
                    "current": "test-1",
                    "nowcast": "test-2",
                    "forecast": "test-3"
                },
                "dateObserved": timestamp
            }
            result = model.run(data, timestamp= timestamp)

            wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:3035', server_path='http://test-etteln.com',flip_coords=False)


            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)

        except Exception as e:
            self.log(unexecore.debug.exception_to_string(e))

    def special_etteln_model(self, args:dict={}):

        sizes = [10,30,50,100,200]

        for size in sizes:
            output_filepath = os.getcwd() + os.sep + 'sim_output/etteln/' +str(size) + os.sep
            model = EttelnModel(output_filepath=output_filepath)

            timestamp = datetime.datetime.now()

            data = {
                "Last72Hour": 100,
                "Last24Hour": 100,
                "Last12Hour": 100,
                "Last4Hour": 100,
                "Last2Hour": 100,
                "LastHour": 100,
                "Forecast2Hour": 100,
                "Forecast0To24": 100,
                "Forecast24To48": 100,
                "Forecast48To72": 100,
                "TrafficLights": {
                    "current": "test-1",
                    "nowcast": "test-2",
                    "forecast": "test-3"
                },
                "dateObserved": timestamp
            }
            result = model.run(data, timestamp=timestamp, asc_scale=size)

            wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:3035', server_path='http://localhost:8000', flip_coords=False)

            with open(output_filepath + 'output_data.json', "w") as f:
                json.dump(wdme_results, f, indent=4)

            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)

    def special_torbay_model(self, args:dict={}):

        sizes = [50,100,200,400]
        sizes = [8]

        for size in sizes:
            output_filepath = os.getcwd() + os.sep + 'sim_output/torbay/' +str(size) + os.sep
            model = TorbayModel(output_filepath=output_filepath)

            timestamp = datetime.datetime.now()

            data = {
                "Last72Hour": 100,
                "Last24Hour": 100,
                "Last12Hour": 100,
                "Last4Hour": 100,
                "Last2Hour": 100,
                "LastHour": 100,
                "Forecast2Hour": 100,
                "Forecast0To24": 100,
                "Forecast24To48": 100,
                "Forecast48To72": 100,
                "TrafficLights": {
                    "current": "test-1",
                    "nowcast": "test-2",
                    "forecast": "test-3"
                },
                "dateObserved": timestamp
            }
            result = model.run(data, timestamp=timestamp, asc_scale=size)

            wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:27700', server_path='http://localhost:8000', flip_coords=True)

            with open(output_filepath + 'output_data.json', "w") as f:
                json.dump(wdme_results, f, indent=4)

            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)


if __name__ == '__main__':
    harness = simulation_Harness()
    #harness.run()
    #harness.special_etteln_model()
    harness.special_torbay_model()