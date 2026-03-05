import flood_simulation.rainfall_model

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

def get_data_filename(filename: str) -> str:
    return os.path.dirname(__file__) + os.sep + 'data' + os.sep + filename

class RainfallBase:
    def __init__(self, output_filepath: str):
        self.land_mask = ''
        self.roughness = ''
        self.infiltration = ''
        self.rain_mask = ''
        self.dem_model = ''

        self.output_filepath = output_filepath

        if self.output_filepath[-1] != os.sep:
            self.output_filepath += os.sep

        if not os.path.exists(self.output_filepath):
            os.makedirs(self.output_filepath)
        else:
            unexecore.file.deltree(self.output_filepath)

        unexecore.file.buildfilepath(self.output_filepath)


    def hist_to_timeseries(self, data: dict) -> dict:
        """
            hist is 72hrs + 1 to start
        """
        timeseries = []
        timeseries.append(0)

        # add data here

        return timeseries

    def nowcast_to_timeseries(self, data: dict) -> dict:
        """
            nowcast is 2hrs + 1 to start
        """
        timeseries = []
        timeseries.append(0)

        # add data here
        return timeseries

    def forecast_to_timeseries(self, data: dict) -> dict:
        """
        forecast is 70hrs + 1 to start
        """
        timeseries = []
        timeseries.append(0)

        #add data here
        return timeseries

    def get_data(self, timestamp: int) -> dict:
        return {}


    def get_path(self) -> str:
        return os.path.dirname(__file__)

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
