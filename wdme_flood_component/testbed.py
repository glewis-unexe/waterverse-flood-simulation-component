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
import etteln_model
import torbay_model

from pip._internal.commands import inspect

os.environ['WATERVERSE_FLOOD_SIM_GPU'] = 'True'

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
    

    def do_stuff(self, rainfall_model:waterverse_rainfall_model.WaterverseRainfallModel, sim_work:dict):        
        for size in sim_work['sizes']:
            for water in sim_work['water_loading']:
                output_filepath = sim_work['root'] + str(size) + os.sep + str(water) + os.sep

                model.init(output_filepath=output_filepath, delete_files=False)
                
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
                sim_results = model.run(data, timestamp=timestamp, asc_scale=size)

                start_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_filepath + 'cafloodpro_GPU_64_2024'), tz=datetime.timezone.utc)

                print(output_filepath)

                current_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_filepath + 'current' + os.sep),tz=datetime.timezone.utc)
                nowcast_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_filepath + 'nowcast' + os.sep),tz=datetime.timezone.utc)
                forcast_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_filepath + 'forecast' + os.sep),tz=datetime.timezone.utc)

                print('\t' + 'current: ' + self.print_timedelta(current_time - start_time))
                print('\t' + 'nowcast: ' + self.print_timedelta(nowcast_time - current_time))
                print('\t' + 'forcast: ' + self.print_timedelta(forcast_time - nowcast_time))

                wdme_results = model.create_wdme_results(sim_results, server_path='http://localhost:8000')

                dump_path = os.getcwd() + os.sep + 'dump'+ os.sep

                unexecore.file.buildfilepath(dump_path)

                dumpfile_root = dump_path + 'output-' + str(size) + '-' + str(water)

                with open(dumpfile_root + '.json', "w") as f:
                    json.dump(wdme_results, f, indent=4)

                for item in wdme_results['data']:
                    with open(dumpfile_root + '-' + item, "w") as f:
                        json.dump(wdme_results['data'][item], f, indent=4)



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

    sim_work = {'sizes': [64], 'water_loading': [5, 10, 25, 75], 'root': os.getcwd() + os.sep + 'sim_output/torbay/new2/'}

    # harness.run()
    # harness.special_etteln_model()
    # harness.special_etteln_model2()
    # harness.special_torbay_model()
    # harness.special_torbay_model2()
    #harness.special_torbay_stats(sim_work)

    model = torbay_model.TorbayModel()
    
    harness.do_stuff(model, sim_work)

    # harness.fix_shonky_torbay_data()