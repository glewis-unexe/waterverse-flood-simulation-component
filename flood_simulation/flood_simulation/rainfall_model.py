import os
import json
import shutil
import datetime
import subprocess
import pyproj

import unexecore.file
import unexecore.time

class Model:
    def __init__(self, output_filepath: str):
        self.land_mask = 'etteln_land_maskv5.asc'
        self.roughness = 'roughnessRates.csv'
        self.infiltration = 'infiltrationRates.csv'
        self.rain_mask = 'etteln_rain_maskv5.asc'
        self.dem_model = 'etteln_demv5.asc'

        self.output_filepath = output_filepath

        if self.output_filepath[-1] != os.sep:
            self.output_filepath += os.sep

        if not os.path.exists(self.output_filepath):
            os.makedirs(self.output_filepath)
        else:
            unexecore.file.deltree(self.output_filepath)

        unexecore.file.buildfilepath(self.output_filepath)

    def create_scenario_file(self, data: dict, filename: str):
        with open(filename, 'w') as f:
            f.write('Name,Spatial Temporal Rain Rates\n')
            f.write('Number Sequences,' + str(len(data)) + '\n')

            for sensor in data:
                text = 'Value' + sensor + ' (mm/hr)'

                time_series = data[sensor]

                for i in range(len(time_series)):
                    text += ', ' + str(time_series[i])

                f.write(text + '\n')

                text = 'Time' + sensor + ' (mm/hr)'

                for i in range(len(time_series)):
                    text += ', ' + str(i * 3600)

                f.write(text + '\n')

    def create_config(self, path: str, run_name: str, total_time: int, follow_on: bool = False, prev_result_filename: str = ''):

        with open(path + run_name + '_config.csv', 'w') as fp:
            fp.write('Simulation Name,test2,,' + '\n')
            fp.write('Short Name (for outputs), ' + run_name + ',,' + '\n')
            fp.write('Version,1,0,0' + '\n')
            fp.write('Time Start (seconds),0,,' + '\n')
            fp.write('Time End   (seconds),' + str(total_time) + ',,' + '\n')
            fp.write('Max DT (seconds),60,,' + '\n')
            fp.write('Min DT (seconds),0.01,,' + '\n')
            fp.write('Update DT (seconds),60,,' + '\n')
            fp.write('Alpha (Fraction DT 0.0-1.0),0.1,,' + '\n')
            #            fp.write('Max Iterations,1000000000,,' + '\n')
            fp.write('Max Iterations,100000000,,' + '\n')
            fp.write('Roughness Global,0,,' + '\n')
            fp.write('Roughness Spatial Temporal,' + self.land_mask + ',' + self.roughness + ',\n')
            fp.write('Infiltration Global (mm/hr),0,,' + '\n')
            fp.write('Infiltration Spatial Temporal,' + self.land_mask + ',' + self.infiltration + ',\n')
            fp.write('Ignore WD (meter),0.0001,,' + '\n')
            fp.write('Tolerance (meter),0.0001,,' + '\n')
            fp.write('Boundary Ele (Hi/Closed-Lo/Open),-9000,,' + '\n')
            fp.write('Elevation ASCII,' + self.dem_model + ' ,,\n')
            fp.write('Water Level Event CSV, ,,' + '\n')
            fp.write('Inflow Event CSV, ,,' + '\n')
            fp.write('Raster Grid CSV,WDrasterParam.csv,,' + '\n')
            fp.write('Output Console, true,,' + '\n')
            fp.write('Output Period (s),3600,,' + '\n')
            fp.write('Output Computation Time, true,,' + '\n')
            fp.write('Check Volumes, true,,' + '\n')
            fp.write('Remove Proc Data (No Pre-Proc), true,,' + '\n')
            fp.write('Remove Pre-Proc Data, true,,' + '\n')
            fp.write('Raster VEL Vector Field, true,,' + '\n')
            fp.write('Raster WD Tolerance (meter),0,,' + '\n')
            fp.write('Update Peak Every DT, false,,' + '\n')
            fp.write('Ignore Upstream, false,,' + '\n')
            fp.write('Upstream Reduction (meter),1,,' + '\n')
            fp.write('Raster Decimal Places,2,,' + '\n')
            fp.write('Rain Spatial Temporal,' + self.rain_mask + ',' + run_name + '_scenario.csv' + '\n')

            # add this for initial depths
            if follow_on:
                fp.write('Initial Water Depths,' + prev_result_filename)

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

    def get_path(self) -> str:
        return os.path.dirname(__file__)

    def run(self, result, timestamp: datetime.datetime):

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

        if scenario_data == {}:
            try:
                if 'data' in result:
                    scenario_data = self.HST_to_sensible(result['data'])

                    if 'TrafficLights' in result['data']:
                        response['TrafficLights'] = {result['data']['TrafficLights']}

            except Exception as e:
                pass

        if scenario_data == {}:
            try:
                if 'sensors' in result:
                    scenario_data = self.HST_to_sensible(result['sensors'])

                    if 'TrafficLights' in result['sensors']:
                        response['TrafficLights'] = {result['sensors']['TrafficLights']}

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

                if 'TrafficLights' in result:
                    response['TrafficLights'] =result['TrafficLights']

            except Exception as e:
                pass

        if scenario_data == {}:
            response['caflood_error'] = 'no valid scenario'
            return response




        for sensor in scenario_data:
            current_scenario[sensor] = self.HST_hist_to_timeseries(scenario_data[sensor])
            nowcast_scenario[sensor] = self.HST_nowcast_to_timeseries(scenario_data[sensor])
            forecast_scenario[sensor] = self.HST_forecast_to_timeseries(scenario_data[sensor])

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

        src_files = ['etteln_demv5.asc',
                     'etteln_land_maskv5.asc',
                     'etteln_rain_maskv5.asc',
                     'infiltrationRates.csv',
                     'roughnessRates.csv',
                     'WDrasterParam.csv'
                     ]
        for file in src_files:
            shutil.copy(src_root + file, path_name + os.sep + file)

        response['caflood_src'] = {}
        response['caflood_src']['dem']  = path_name + os.sep + src_files[0]
        response['caflood_src']['land'] = path_name + os.sep + src_files[1]
        response['caflood_src']['rain'] = path_name + os.sep + src_files[2]

        src_root = self.get_path() + os.sep + 'data/'

        src_files = ['cafloodpro_GPU_64',
                     'caFloodPro_license.txt',
                     'cafloodpro_GPU_64_2024',
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

        #gpu
        response['caflood_exe'] = 'cafloodpro_GPU_64_2024'

        for scenario in scenarios:
            response[scenario] = {}
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

def get_data_filename(filename: str) -> str:
    return os.path.dirname(__file__) + os.sep + 'data' + os.sep + filename
