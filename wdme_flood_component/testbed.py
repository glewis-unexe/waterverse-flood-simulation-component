import os
import datetime
import inspect
import time

import unexecore.testharness
import unexecore.debug
import unexecore.logger
import unexecore.time
import unexecore.file
import json
import datetime

import waterverse_rainfall_model

from pip._internal.commands import inspect

os.environ['WATERVERSE_FLOOD_SIM_GPU'] = 'True'


class EttelnModel(waterverse_rainfall_model.WaterverseRainfallModel):
    def __init__(self, output_filepath: str,delete_files:bool):
        super().__init__(output_filepath,delete_files)

        self.dem_model = 'etteln_demv5.asc'
        self.land_mask = 'etteln_land_maskv5.asc'
        self.rain_mask = 'etteln_rain_maskv5.asc'
        self.infiltration = 'infiltrationRates.csv'
        self.roughness = 'roughnessRates.csv'

        self.location_src_root = os.getcwd() + os.sep + 'locations/etteln/'

    def setup_rainfall_scenario_data(self, result: dict):
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
    def __init__(self, output_filepath: str, delete_files):
        super().__init__(output_filepath, delete_files)

        self.land_mask = 'catchment_landcover_8m.asc'
        self.rain_mask = 'catchment_mask_8m.asc'
        self.dem_model = 'catchment_dem_8m.asc'

        self.roughness = 'roughnesses.csv'
        self.infiltration = 'infiltration.csv'

        self.location_src_root = os.getcwd() + os.sep + 'locations/torbay/'

        self.src_coords = 'EPSG:27700'
        self.flip_coords = True

    def setup_rainfall_scenario_data(self, result: dict):
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
                    # '3': result, #3 is the mask
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
            unexecore.logger.logger.log(inspect.currentframe(), unexecore.debug.exception_to_string(e))
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
            unexecore.logger.logger.log(inspect.currentframe(), unexecore.debug.exception_to_string(e))

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
            result = model.run(data, timestamp=timestamp, asc_scale=100)

            wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:27700',
                                                                        server_path='http://test.com', flip_coords=True)
            print()

            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)


        except Exception as e:
            unexecore.logger.logger.log(inspect.currentframe(), unexecore.debug.exception_to_string(e))

    def etteln_model(self, args: dict):
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
            result = model.run(data, timestamp=timestamp)

            wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:3035',
                                                                        server_path='http://test-etteln.com',
                                                                        flip_coords=False)

            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)

        except Exception as e:
            self.log(unexecore.debug.exception_to_string(e))

    def special_etteln_model(self, args: dict = {}):

        sizes = [10, 30, 50, 100, 200]

        for size in sizes:
            output_filepath = os.getcwd() + os.sep + 'sim_output/etteln/' + str(size) + os.sep
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

            wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:3035',
                                                                        server_path='http://localhost:8000',
                                                                        flip_coords=False)

            with open(output_filepath + 'output_data.json', "w") as f:
                json.dump(wdme_results, f, indent=4)

            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)

    def special_etteln_model2(self, args: dict = {}):

        sizes = [50, 30, 15]

        water_loading = [25, 50, 100, 200]

        for size in sizes:

            for water in water_loading:
                output_filepath = os.getcwd() + os.sep + 'sim_output/etteln/' + str(size) + os.sep + str(water) + os.sep
                model = EttelnModel(output_filepath=output_filepath)

                timestamp = datetime.datetime.now()

                data = {
                    "Last72Hour": water,
                    "Last24Hour": water,
                    "Last12Hour": water,
                    "Last4Hour": water,
                    "Last2Hour": water,
                    "LastHour": water,
                    "Forecast2Hour": water,
                    "Forecast0To24": water,
                    "Forecast24To48": water,
                    "Forecast48To72": water,
                    "TrafficLights": {
                        "current": "test-1",
                        "nowcast": "test-2",
                        "forecast": "test-3"
                    },
                    "dateObserved": timestamp
                }
                time0 = time.time()
                result = model.run(data, timestamp=timestamp, asc_scale=size)
                wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:3035',
                                                                            server_path='http://localhost:8000',
                                                                            flip_coords=False)

                with open(output_filepath + 'output_data.json', "w") as f:
                    json.dump(wdme_results, f, indent=4)

                for item in wdme_results['data']:
                    with open(output_filepath + item, "w") as f:
                        json.dump(wdme_results['data'][item], f, indent=4)

                time0 = time.time() - time0

                print(output_filepath + ' took' + str(int(time0)) + 's')

    def special_torbay_model(self, args: dict = {}):

        sizes = [50, 100, 200, 400]
        sizes = [8]

        for size in sizes:
            output_filepath = os.getcwd() + os.sep + 'sim_output/torbay/' + str(size) + os.sep
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

            wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:27700',
                                                                        server_path='http://localhost:8000',
                                                                        flip_coords=True)

            with open(output_filepath + 'output_data.json', "w") as f:
                json.dump(wdme_results, f, indent=4)

            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)

    def special_torbay_model2(self, args: dict = {}):

        sizes = [8, 16, 32, 64]

        water_loading = [5, 10, 25, 75]

        for size in sizes:

            for water in water_loading:
                output_filepath = os.getcwd() + os.sep + 'sim_output/torbay/new2/' + str(size) + os.sep + str(
                    water) + os.sep
                model = TorbayModel(output_filepath=output_filepath)

                timestamp = datetime.datetime.now()

                data = {
                    "Last72Hour": water,
                    "Last24Hour": water,
                    "Last12Hour": water,
                    "Last4Hour": water,
                    "Last2Hour": water,
                    "LastHour": water,
                    "Forecast2Hour": water,
                    "Forecast0To24": water,
                    "Forecast24To48": water,
                    "Forecast48To72": water,
                    "TrafficLights": {
                        "current": "test-1",
                        "nowcast": "test-2",
                        "forecast": "test-3"
                    },
                    "dateObserved": timestamp
                }
                time0 = time.time()
                result = model.run(data, timestamp=timestamp, asc_scale=size)
                wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:27700',
                                                                            server_path='http://localhost:8000',
                                                                            flip_coords=True)

                with open(output_filepath + 'output_data.json', "w") as f:
                    json.dump(wdme_results, f, indent=4)

                for item in wdme_results['data']:
                    with open(output_filepath + item, "w") as f:
                        json.dump(wdme_results['data'][item], f, indent=4)

                time0 = time.time() - time0

                print(output_filepath + ' took' + str(int(time0)) + 's')

    def fix_shonky_torbay_data(self):
        result = {
            "TrafficLights": {
                "current": "test-1", "forecast": "test-3", "nowcast": "test-2"
            },
            "caflood_exe": "cafloodpro_GPU_64_2024",
            "caflood_src": {
                "dem": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/catchment_dem_8m.asc",
                "land": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/catchment_landcover_8m.asc",
                "rain": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/catchment_mask_8m.asc"
            },
            "current": {
                "caflood_response": 0,
                "peak": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/current/current_WDrasterParam_PEAK.asc"
            },
            "forecast": {
                "caflood_response": 0,
                "1day": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/forecast/forecast_WDrasterParam_86400.asc",
                "2day": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/forecast/forecast_WDrasterParam_172800.asc",
                "end": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/forecast/forecast_WDrasterParam_252000.asc",
                "peak": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/forecast/forecast_WDrasterParam_PEAK.asc"
            },
            "nowcast": {
                "caflood_response": 0,
                "peak": "/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/nowcast/nowcast_WDrasterParam_PEAK.asc"
            },
            "timestamp": "2026-04-28T10:20:51Z"
        }
        sizes = [8, 50, 100, 200, 400]

        water_loading = [1, 2, 50, 100]

        for size in sizes:

            for water in water_loading:
                output_filepath = os.getcwd() + os.sep + 'sim_output/torbay/new/' + str(size) + os.sep + str(
                    water) + os.sep

                print(output_filepath)

                result['caflood_src']['dem'] = output_filepath + 'catchment_dem_8m.asc'
                result['caflood_src']['land'] = output_filepath + 'catchment_landcover_8m.asc'
                result['caflood_src']['rain'] = output_filepath + 'catchment_mask_8m.asc'

                result['current']['peak'] = output_filepath + 'current/current_WDrasterParam_PEAK.asc'

                result['nowcast']['peak'] = output_filepath + 'nowcast/nowcast_WDrasterParam_PEAK.asc'

                result['forecast']["1day"] = output_filepath + 'forecast/forecast_WDrasterParam_86400.asc'
                result['forecast']["2day"] = output_filepath + 'forecast/forecast_WDrasterParam_172800.asc'
                result['forecast']["end"] = output_filepath + 'forecast/forecast_WDrasterParam_252000.asc'
                result['forecast']["peak"] = output_filepath + 'forecast/forecast_WDrasterParam_PEAK.asc'

                wdme_results = flood_simulation.wdme_results.create_results(result, src_coords='EPSG:27700',server_path='http://localhost:8000',flip_coords=True)

                with open(output_filepath + 'output_data-fixed.json', "w") as f:
                    json.dump(wdme_results, f, indent=4)

                for item in wdme_results['data']:
                    with open(output_filepath + item, "w") as f:
                        json.dump(wdme_results['data'][item], f, indent=4)

    def special_torbay_stats(self, sim_work:dict):
        sizes = [8, 16, 32, 64]
        water_loading = [5, 10, 25, 75]

        """
        timestamps
            start - cafloodpro_GPU_64_2024
            time to run current = start - current/
            time to run nowcast = nowcast/ - current/
            time to run forecast = forecast/ - current/

        """

        for size in sim_work['sizes']:
            for water in sim_work['water_loading']:
                output_filepath = sim_work['root'] + str(size) + os.sep + str(water) + os.sep

                model = TorbayModel(output_filepath=output_filepath, delete_files=False)

                start_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_filepath + 'cafloodpro_GPU_64_2024'), tz=datetime.timezone.utc)

                print(output_filepath)

                current_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_filepath + 'current' + os.sep),tz=datetime.timezone.utc)
                nowcast_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_filepath + 'nowcast' + os.sep),tz=datetime.timezone.utc)
                forcast_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_filepath + 'forecast' + os.sep),tz=datetime.timezone.utc)

                print('\t' + 'current: ' + self.print_timedelta(current_time - start_time))
                print('\t' + 'nowcast: ' + self.print_timedelta(nowcast_time - current_time))
                print('\t' + 'forcast: ' + self.print_timedelta(forcast_time - nowcast_time))

                sim_results = model.create_empty_simulation_results()

                wdme_results = model.create_wdme_results(sim_results, server_path='http://localhost:8000')

                dump_path = os.getcwd() + os.sep + 'dump'+ os.sep

                unexecore.file.buildfilepath(dump_path)

                dumpfile_root = dump_path + 'output-' + str(size) + '-' + str(water)

                with open(dumpfile_root + '.json', "w") as f:
                    json.dump(wdme_results, f, indent=4)

                for item in wdme_results['data']:
                    with open(dumpfile_root + '-' + item, "w") as f:
                        json.dump(wdme_results['data'][item], f, indent=4)



    def print_timedelta(self, td: datetime.timedelta) -> str:

        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2) + ' -> ' + str((hours * 60) + minutes).zfill(3)


if __name__ == '__main__':
    harness = simulation_Harness()

    sim_work = {
        'sizes': [8, 16, 32, 64],
        'water_loading': [5, 10, 25, 75],
        'root': os.getcwd() + os.sep + 'sim_output/torbay/new2/'
    }

    sim_work = {
        'sizes': [64],
        'water_loading': [5, 10, 25, 75],
        'root': '/home/gareth/Documents/dev/work/waterverse/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbat-new2/'
    }

    # harness.run()
    # harness.special_etteln_model()
    # harness.special_etteln_model2()
    # harness.special_torbay_model()
    # harness.special_torbay_model2()
    harness.special_torbay_stats(sim_work)

    # harness.fix_shonky_torbay_data()