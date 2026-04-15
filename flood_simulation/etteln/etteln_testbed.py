import unexe_flood_simulation.weatherapi_model
import unexe_flood_simulation.wdme_results
import os
import json
import shutil
import datetime
import subprocess
import time

import unexecore.ascfile
import unexecore.file
import unexecore.time
import unexecore.debug

class WeatherapiModel2 (unexe_flood_simulation.weatherapi_model.Weatherapi_Model):
    def __init__(self, output_filepath: str):
        super().__init__(output_filepath)

        self.land_mask = 'catchment_landcover_8m.asc'
        self.rain_mask = 'catchment_mask_8m.asc'
        self.dem_model = 'catchment_dem_8m.asc'

        self.roughness = 'roughnesses.csv'
        self.infiltration = 'infiltration.csv'

        self.duration_in_days = 3

        self.loc = '50.4355, -3.565'

    def run(self, timestamp: datetime.datetime, asc_scale:int=-1):

        response = {}
        response['TrafficLights'] = {
            "current": "none",
            "nowcast": "none",
            "forecast": "none"
        }

        response['timestamp'] = unexecore.time.datetime_to_fiware(timestamp)

        current_scenario = {}
        nowcast_scenario = {}
        forecast_scenario = {}

        scenario_data = {}

        """
        create scenario data from weatherapi calls
        and map to the 5 sensors (could just map to 1 here ...)
        """

        try:
            rainfall_data = self.get_data(timestamp)

            scenario_data = {
                '2169': rainfall_data,
                '2172': rainfall_data,
                '2173': rainfall_data,
                '2174': rainfall_data,
                '2175': rainfall_data
            }

        except Exception as e:
            pass

        if scenario_data == {}:
            response['caflood_error'] = 'no valid scenario'
            return response

        for sensor in scenario_data:
            """
                current_scenario is first 3 days
                nowcast_scenario is next couple of hours
                forecast_scenario is next couple of days after
            """
            current_scenario[sensor] = self.hist_to_timeseries(scenario_data[sensor])
            assert len(current_scenario[sensor]) == 73

            nowcast_scenario[sensor] = self.nowcast_to_timeseries(scenario_data[sensor])
            assert len(nowcast_scenario[sensor]) == 3

            forecast_scenario[sensor] = self.forecast_to_timeseries(scenario_data[sensor])
            assert len(forecast_scenario[sensor]) == 71

        path_name = self.output_filepath
        if not os.path.exists(path_name):
            os.makedirs(path_name)
        else:
            unexecore.file.deltree(path_name)

        unexecore.file.buildfilepath(path_name + os.sep + 'current' + os.sep)
        unexecore.file.buildfilepath(path_name + os.sep + 'nowcast' + os.sep)
        unexecore.file.buildfilepath(path_name + os.sep + 'forecast' + os.sep)

        unexecore.file.deltree(path_name + os.sep + 'current' + os.sep)
        unexecore.file.deltree(path_name + os.sep + 'nowcast' + os.sep)
        unexecore.file.deltree(path_name + os.sep + 'forecast' + os.sep)

        src_root = self.get_path() + os.sep + 'data/CaddiesInput/'

        src_root = os.getcwd() + os.sep

        #copy reference files to input folder for running simulation
        src_files = [self.dem_model,
                    self.land_mask,
                    self.rain_mask,
                    self.roughness,

                    self.infiltration,
                     'WDrasterParam.csv'
                     ]
        for file in src_files:

            if asc_scale != -1 and '.asc' in file:
                asc = unexecore.ascfile.ASCFile(src_root + file)
                new_asc = asc.scale(asc_scale)
                new_asc.save(path_name + os.sep + file)
            else:
                shutil.copy(src_root + file, path_name + os.sep + file)

        response['caflood_src'] = {}
        response['caflood_src']['dem']  = path_name + os.sep + self.dem_model
        response['caflood_src']['land'] = path_name + os.sep + self.land_mask
        response['caflood_src']['rain'] = path_name + os.sep + self.rain_mask

        src_root = self.get_path() + os.sep + 'data/'

        src_files = ['cafloodpro_GPU_64_2024',
                     'cafloodpro_64'
                     ]

        for file in src_files:
            shutil.copy(src_root + file, path_name + os.sep + file)

        self.create_scenario_file(current_scenario, path_name + os.sep + 'current_scenario.csv')
        self.create_scenario_file(nowcast_scenario, path_name + os.sep + 'nowcast_scenario.csv')
        self.create_scenario_file(forecast_scenario, path_name + os.sep + 'forecast_scenario.csv')

        self.create_config(path_name + os.sep, 'current', 259200, False)
        self.create_config(path_name + os.sep, 'nowcast', 7200, True, 'current/current_WDrasterParam_259200.asc')
        self.create_config(path_name + os.sep, 'forecast', 252000, True, 'nowcast/nowcast_WDrasterParam_7200.asc')

        scenarios = ['current', 'nowcast', 'forecast']

        file_timestamp = unexecore.time.datetime_to_fiware(timestamp)

        #cpu
        response['caflood_exe'] = 'cafloodpro_64'

        if 'WATERVERSE_FLOOD_SIM_GPU' in os.environ and os.environ['WATERVERSE_FLOOD_SIM_GPU'].lower() == 'true':
            #gpu
            response['caflood_exe'] = 'cafloodpro_GPU_64_2024'

        for scenario in scenarios:
            response[scenario] = {}

            with open(path_name+os.sep+scenario +'.sh','w') as f:
                f.write(path_name + '/' + response['caflood_exe']
                        + ' '
                        + '-WCA2D'
                        + ' '
                        + path_name
                        + ' '
                        +scenario + '_config.csv'
                        + ' '
                        + path_name + os.sep + scenario + os.sep)

            os.chmod(path_name + os.sep + scenario +'.sh', 0o755)

            process_result = subprocess.run([path_name + '/' + response['caflood_exe'],
                                             '-WCA2D',
                                             path_name,
                                             scenario + '_config.csv',
                                             path_name + os.sep + scenario + os.sep
                                             ],
                                            stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL
                                            )

            response[scenario]['caflood_response'] = process_result.returncode
            if response[scenario]['caflood_response'] != 0:

                response[scenario]['caflood_error'] = 'CAFlood failure:'
                if process_result.stderr:
                    response[scenario]['caflood_error'] += 'STDERR:' + process_result.stderr.decode('utf-8')
                if process_result.stdout:
                    response[scenario]['caflood_error'] += 'STDOUT:' + process_result.stdout.decode('utf-8')
            else:
                root_dir = path_name + os.sep + scenario + os.sep
                response[scenario]['peak'] = root_dir + os.sep + scenario + '_WDrasterParam_PEAK.asc'

                if scenario == 'forecast':
                    timestamps = {'1day': '86400', '2day': '172800', 'end': '252000'}

                    for key in timestamps:
                        response[scenario][key] = root_dir + os.sep + scenario + '_WDrasterParam_' + timestamps[key] + '.asc'
        return response



class EttelnTestData(WeatherapiModel2):
    def __init__(self, output_filepath: str):

        super().__init__(output_filepath)

        self.land_mask = 'etteln_land_maskv5.asc'
        self.rain_mask = 'etteln_rain_maskv5.asc'
        self.dem_model = 'etteln_demv5.asc'

        self.roughness = 'roughnessRates.csv'
        self.infiltration = 'infiltrationRates.csv'

        self.duration_in_days = 3

        self.loc = '51.63, 8.76'
        self.rainlist = {}

    def get_data(self, current_date:datetime.datetime):

        #this needs to return 144 timestamp data points

        return self.rainlist

    def set_data(self, data:dict):
        #convert the HST data into a single timeseries

        if 'Last72Hour' not in data:
            print()

        #current data
        last_2_days = data['Last72Hour'] - data['Last24Hour']
        last_day = data['Last24Hour'] - data['Last12Hour']
        last_12 = data['Last12Hour'] - data['Last4Hour']
        last_4 = data['Last4Hour'] - data['Last2Hour']
        last_2 = data['Last2Hour'] - data['LastHour']
        last_1 = data['LastHour']

        self.rainlist = {}

        index = 1
        for i in range(0, 48):
            self.rainlist[str(index)] = round(last_2_days / 48, 2)
            index += 1

        for i in range(0, 12):
            self.rainlist[str(index)] = round(last_day / 12, 2)
            index += 1

        for i in range(0, 8):
            self.rainlist[str(index)] = round(last_12 / 8, 2)
            index += 1

        for i in range(0, 2):
            self.rainlist[str(index)] = round(last_4 / 2, 2)
            index += 1

        self.rainlist[str(index)] = round(last_2, 2)
        index += 1

        self.rainlist[str(index)] = round(last_1, 2)
        index += 1

        #nowcast
        self.rainlist[str(index)] = round(data['Forecast2Hour'] / 2, 2)
        index += 1
        self.rainlist[str(index)] = round(data['Forecast2Hour'] / 2, 2)
        index += 1

        #forecast
        for i in range(0, 22):
            self.rainlist[str(index)] = round((data['Forecast0To24'] - data['Forecast2Hour']) / 24, 2)
            index += 1

        for i in range(0, 24):
            self.rainlist[str(index)] = round(data['Forecast24To48'] / 24, 2)
            index += 1

        for i in range(0, 24):
            self.rainlist[str(index)] = round(data['Forecast48To72'] / 24, 2)
            index += 1

        print()


import waterverse_sdg.sdg as sdg
import unexecore.testharness
import unexecore.debug

class etteln_Harness(unexecore.testharness.TestHarness):
    def __init__(self):
        super().__init__()

        option_id = 1

        self.output_filepath = os.getcwd() + os.sep + 'output' + os.sep
        self.model = unexe_flood_simulation.rainfall_model.Model(output_filepath=self.output_filepath)

        self.pilot = 'etteln'

        # create the options for the test harness, using the scenarios from the ettlen attributes
        # do the core loop twice, firstly to build a set of options for generating results locally
        # and secondly to create the HTTP calls for the WDME flood component
        try:
            start_date = unexecore.time.datetime_to_fiware(datetime.datetime.now(datetime.timezone.utc).replace(minute=0, hour=0, second=0, microsecond=0))
            datapath = sdg.get_datapath() + os.sep

            sdg.add_pilot(self.pilot)

            sdg.add_sensor_to_pilot(self.pilot, 'test', json.load(open(datapath + 'etteln_payload.json')))
            sdg.reset_pilot(self.pilot, start_date)

            #'scenarios' are implicit components of the SDG and stored in each attribute.
            #so, picking an attribute and extracting the scenario names will give the key data we need
            for scenario in sdg.pilot_model[self.pilot]['test']['config']['attributes'][0]['range']:
                self.options[str(option_id)] = {'label': 'Local Scenario: '+ scenario['name'], 'function': self.std_model,'args':{'scenario': scenario['name']} }
                option_id += 1

            self.options[str(option_id)] = {'label': 'WeatherAPI live', 'function': self.run_weatherapi, 'args': {}}
            option_id += 1

        except Exception as e:
            self.log('SDG: Failed to start-up ' + self.pilot + ' ' + unexecore.debug.exception_to_string(e))


    def run_weatherapi(self, args:dict):
        t0 = time.time()

        try:
            output_filepath = os.getcwd() + os.sep + 'output' + os.sep
            unexecore.file.buildfilepath(output_filepath)
            model = WeatherapiModel2(output_filepath=output_filepath)
            model.land_mask = 'etteln_land_maskv5.asc'
            model.rain_mask = 'etteln_rain_maskv5.asc'
            model.dem_model = 'etteln_demv5.asc'
            model.roughness = 'roughnessRates.csv'
            model.infiltration = 'infiltrationRates.csv'

            model.loc = '51.63, 8.76'

            result = model.run(datetime.datetime.now(datetime.timezone.utc), asc_scale=120)
            wdme_results = unexe_flood_simulation.wdme_results.create_results(result, source_coords='EPSG:3035', flip_coords=False, server_path='http://whatever.com')

            for item in wdme_results['data']:
                with open(output_filepath + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)

        except Exception as e:
            print(unexecore.debug.exception_to_string(e))

        print('Load:' + str(round(time.time() - t0, 2)))

    def summarise_info(self, info:dict) -> str:
        keys = list(info.keys())

        if len(keys) == 1:
            if keys[0] < 0.1:
                return 'Dry'

            if keys[0] < 2.0:
                return 'Mainly rainy'

            return 'Very rainy'

        return 'Unsettled'

    def summarise_flood_map_info(self, info:dict) -> str:

        keys = list(info.keys())

        passable = 0 # < 0.1m ?
        caution = 0 #  < 0.3m
        flooded = 0 # > 0.3m

        for key in keys:
            if key <= 0.1:
                passable += info[key]
            else:
                if key <= 0.3:
                    caution += info[key]
                else:
                    flooded += info[key]

        return  'passable: ' + str(passable) +' caution: ' +str(caution) +' flooded: ' + str(flooded) + ' of' + str(passable+caution+flooded)



    def std_model(self, args:dict):

        t0 = time.time()

        try:
            current_date = datetime.datetime.now(datetime.timezone.utc)
            sdg.set_current_state(self.pilot, 'test', {"mode": args['scenario']})

            data = sdg.get_data(self.pilot, 'test', 1)

            output_filepath = os.getcwd() + os.sep + 'WeatherAnalysis' + os.sep
            unexecore.file.buildfilepath(output_filepath)

            model = EttelnTestData(output_filepath=output_filepath)
            model.set_data(data[0])

            data = model.get_data(current_date)
            """
                analyse rainfall
                last 3 days - range(0,72) steps
                next 2hrs - range(72,74) steps
                next 3 days - 2hrs range(74,144) steps
                
                rain 0<1
                     1.1-4
                     >4
            """

            ranges = [{'label': '3 days ago', 'range': [0,24]},
                      {'label': '2 days ago', 'range': [24,48]},
                      {'label': '1 days ago', 'range': [48,72]},
                      {'label': 'Now cast', 'range': [72,74]},
                      {'label': 'Next 24hrs', 'range': [72,96]},
                      {'label': 'Tomorrow', 'range': [96,120]},
                      {'label': 'Next Day', 'range': [120,144]}
                      ]
            keys = list(data.keys())

            for r in ranges:
                info = {}

                for i in range(r['range'][0],r['range'][1]):
                    val = data[keys[i]]
                    if val not in info:
                        info[val] = 0

                    info[val] += 1

                print(r['label'] + ' ' + str(info) + ' ' + self.summarise_info(info))

            resolutions = [20,30,50,100,250]

            for res in resolutions:
                t1 = time.time()
                result = model.run(timestamp=current_date,asc_scale=res)
                print(str(res)+'m took:' + str(round(time.time() - t1, 2)))

            if False: #generate output data?
                wdme_results = unexe_flood_simulation.wdme_results.create_results(result, source_coords='EPSG:3035', flip_coords=False, server_path='http://whatever.com')
                for item in wdme_results['data']:
                    with open(output_filepath + item, "w") as f:
                        json.dump(wdme_results['data'][item], f, indent=4)

                        info = {}

                        for feature in wdme_results['data'][item]['features']:

                            if 'depth' in feature['properties']:
                                val = feature['properties']['depth']
                                if val not in info:
                                    info[val] = 0

                                info[val] += 1

                        if info != {}:
                            print(item + ' ' + self.summarise_flood_map_info(info))

        except Exception as e:
            self.log(unexecore.debug.exception_to_string(e))

        print('Load:' + str(round(time.time() - t0,2)) )

    def log(self, text):
        print(text)

if __name__ == '__main__':
    harness = etteln_Harness()
    harness.run()