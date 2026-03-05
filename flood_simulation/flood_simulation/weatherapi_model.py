import flood_simulation.rainfall_base

import os
import json
import shutil
import datetime
import subprocess
import requests

import unexecore.ascfile
import unexecore.file
import unexecore.time
import unexecore.debug


class Weatherapi_Model(flood_simulation.rainfall_base.RainfallBase):
    def __init__(self, output_filepath: str):
        super().__init__(output_filepath)

        self.land_mask = 'etteln_land_maskv5.asc'
        self.rain_mask = 'etteln_rain_maskv5.asc'
        self.dem_model = 'etteln_demv5-100.asc'

        self.roughness = 'roughnessRates.csv'
        self.infiltration = 'infiltrationRates.csv'


        self.duration_in_days = 3

        self.loc = '51.63, 8.76'

    def hist_to_timeseries(self, data: dict) -> dict:
        """
            hist is 72hrs + 1 to start
        """
        timeseries = []
        timeseries.append(0)

        labels = list(data.keys())
        labels.sort()

        for i in range(0,72):
            timeseries.append(data[labels[i]] +20)

        # add data here

        return timeseries

    def nowcast_to_timeseries(self, data: dict) -> dict:
        """
            nowcast is 2hrs + 1 to start
        """
        timeseries = []
        timeseries.append(0)

        # add data here
        labels = list(data.keys())
        labels.sort()

        for i in range(72, 74):
            timeseries.append(data[labels[i]] +20)

        return timeseries

    def forecast_to_timeseries(self, data: dict) -> dict:
        """
        forecast is 70hrs + 1 to start
        """
        timeseries = []
        timeseries.append(0)

        #add data here
        labels = list(data.keys())
        labels.sort()

        for i in range(74, 144):
            timeseries.append(data[labels[i]] +20)

        return timeseries


    def get_data(self, current_date:datetime.datetime):
        rainlist = {}

        try:
            date = unexecore.time.datetime_to_date(current_date - datetime.timedelta(days=self.duration_in_days))

            weatherapi_now_time = str(current_date.year) + '-' + str(current_date.month).zfill(2) + '-' + str(current_date.day).zfill(2) + ' ' + str(current_date.hour).zfill(2) + ':' + '00'

            request_url = 'http://api.weatherapi.com/v1/history.json?key=' + os.environ['WEATHERAPI_KEY'] + '&q='
            request_url += self.loc
            request_url += '&dt=' + date
            request_url += '&end_dt=' + unexecore.time.datetime_to_date(current_date)
            request_url += '&aqi=' + 'no'
            request_url += '&alerts=' + 'no'

            r = requests.get(request_url)

            if r.status_code == 200:

                weather_data = json.loads(r.text)
                for day in weather_data['forecast']['forecastday']:
                    for hour in day['hour']:
                        if hour['time'] < weatherapi_now_time:
                            rainlist[hour['time']] = hour['precip_mm']

                # forecast
                request_url = 'http://api.weatherapi.com/v1/forecast.json?key=' + os.environ['WEATHERAPI_KEY'] + '&q='
                request_url += self.loc
                request_url += '&days=' + str(self.duration_in_days)
                request_url += '&aqi=' + 'no'
                request_url += '&alerts=' + 'no'

                r = requests.get(request_url)

                if r.status_code == 200:

                    weather_data = json.loads(r.text)

                    for day in weather_data['forecast']['forecastday']:
                        for hour in day['hour']:

                            if hour['time'] >= weatherapi_now_time:
                                rainlist[hour['time']] = hour['precip_mm']
        except Exception as e:
            print(unexecore.debug.exception_to_string(e))

        return rainlist

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
