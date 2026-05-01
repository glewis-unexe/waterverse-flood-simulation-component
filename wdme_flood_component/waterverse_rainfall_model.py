import os
import math
import json
import shutil
import datetime
import subprocess
from urllib import response

import pyproj

import unexecore.file
import unexecore.time
import unexecore.ascfile


class WaterverseRainfallModel:
    def __init__(self, output_filepath: str,delete_files=False):
        self.land_mask = 'etteln_land_maskv5.asc'
        self.roughness = 'roughnessRates.csv'
        self.infiltration = 'infiltrationRates.csv'
        self.rain_mask = 'etteln_rain_maskv5.asc'
        self.dem_model = 'etteln_demv5.asc'
        self.location_src_root = ''
        self.current_scenario = {}
        self.nowcast_scenario = {}
        self.forecast_scenario = {}

        #coords for output WDME visualisation data
        self.src_coords = 'EPSG:27700'
        self.flip_coords = False

        self.output_filepath = output_filepath

        if self.output_filepath[-1] != os.sep:
            self.output_filepath += os.sep

        if not os.path.exists(self.output_filepath):
            os.makedirs(self.output_filepath)
        else:
            if delete_files:
                unexecore.file.deltree(self.output_filepath)

        unexecore.file.buildfilepath(self.output_filepath)

    def setup_rainfall_scenario_data(self, result: dict) -> bool:
        self.current_scenario = {}
        self.nowcast_scenario = {}
        self.forecast_scenario = {}

        return False

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

    def create_config(self, path: str, run_name: str, total_time: int, follow_on: bool = False,
                      prev_result_filename: str = ''):

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

    def get_path(self) -> str:
        return os.path.dirname(__file__)

    def run(self, result, timestamp: datetime.datetime, asc_scale: int = -1):

        response = {}
        response['TrafficLights'] = {
            "current": "none",
            "nowcast": "none",
            "forecast": "none"
        }

        response['timestamp'] = unexecore.time.datetime_to_fiware(timestamp)

        if 'TrafficLights' in result:
            response['TrafficLights'] = result['TrafficLights']

        if self.setup_rainfall_scenario_data(result) == False:
            response['caflood_error'] = 'no valid scenario'
            return response

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

        src_files = [self.dem_model,
                     self.land_mask,
                     self.rain_mask,
                     self.infiltration,
                     self.roughness,
                     'WDrasterParam.csv'
                     ]
        for file in src_files:
            if asc_scale != -1 and '.asc' in file:
                asc = unexecore.ascfile.ASCFile(self.location_src_root + file)
                new_asc = asc.scale(asc_scale)
                new_asc.save(path_name + os.sep + file)
            else:
                shutil.copy(self.location_src_root + file, path_name + os.sep + file)

        response['caflood_src'] = {}
        response['caflood_src']['dem'] = path_name + os.sep + src_files[0]
        response['caflood_src']['land'] = path_name + os.sep + src_files[1]
        response['caflood_src']['rain'] = path_name + os.sep + src_files[2]

        src_root = self.get_path() + os.sep + 'data/'

        src_files = ['cafloodpro_GPU_64_2024',
                     'cafloodpro_64'
                     ]

        for file in src_files:
            shutil.copy(src_root + file, path_name + os.sep + file)

        self.create_scenario_file(self.current_scenario, path_name + os.sep + 'current_scenario.csv')
        self.create_scenario_file(self.nowcast_scenario, path_name + os.sep + 'nowcast_scenario.csv')
        self.create_scenario_file(self.forecast_scenario, path_name + os.sep + 'forecast_scenario.csv')

        self.create_config(path_name + os.sep, 'current', 259200, False)
        self.create_config(path_name + os.sep, 'nowcast', 7200, True, 'current/current_WDrasterParam_259200.asc')
        self.create_config(path_name + os.sep, 'forecast', 252000, True, 'nowcast/nowcast_WDrasterParam_7200.asc')

        scenarios = ['current', 'nowcast', 'forecast']

        file_timestamp = unexecore.time.datetime_to_fiware(timestamp)

        # cpu
        response['caflood_exe'] = 'cafloodpro_64'

        if 'WATERVERSE_FLOOD_SIM_GPU' in os.environ and os.environ['WATERVERSE_FLOOD_SIM_GPU'].lower() == 'true':
            # gpu
            response['caflood_exe'] = 'cafloodpro_GPU_64_2024'

        for scenario in scenarios:
            response[scenario] = {}

            with open(path_name + os.sep + scenario + '.sh', 'w') as f:
                f.write(path_name + '/' + response['caflood_exe']
                        + ' '
                        + '-WCA2D'
                        + ' '
                        + path_name
                        + ' '
                        + scenario + '_config.csv'
                        + ' '
                        + path_name + os.sep + scenario + os.sep)

            os.chmod(path_name + os.sep + scenario + '.sh', 0o755)

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
                        response[scenario][key] = root_dir + os.sep + scenario + '_WDrasterParam_' + timestamps[
                            key] + '.asc'
        return response

    def create_wdme_results(self, flood_result: dict, server_path: str = None) -> dict:
        wdme_result = {
            # results to return to user
            'result':
                {
                    "timestamp": flood_result["timestamp"],
                    "traffic_lights": {
                        "current": "<set>",
                        "nowcast": "<set>",
                        "forecast": "<set>",
                        "text": {
                            "current": 'Not known at this time',
                            "nowcast": 'Not known at this time',
                            "forecast": 'Not known at this time'
                        }
                    },
                    "color_key": [
                        {
                            "text": "<0.1m",
                            "color": "#ffffff"
                        },
                        {
                            "text": "0.1-0.3m",
                            "color": "#ff8c00"
                        },
                        {
                            "text": ">0.3m",
                            "color": "#ff1414"
                        }
                    ],
                    "geojson": []
                },
            # data to return through API call
            'data': {
            }
        }

        colour_lookup = {}
        colour_lookup[0.099] = (255, 255, 255, 0)
        colour_lookup[0.31] = (255, 140, 0, 255)
        colour_lookup[9999999.0] = (255, 20, 20, 255)

        # this should be the blue scale that is normally used
        if False:
            wdme_result['result']['color_key'] = [
                {
                    "text": "<0.1m",
                    "color": "#ffffff"
                },
                {
                    "text": "0.1-0.5m",
                    "color": "#ceecfe"
                },
                {
                    "text": "0.5-1.0m",
                    "color": "#9ccbfe"
                },
                {
                    "text": "1.0-2.0m",
                    "color": "#7299fe"
                },
                {
                    "text": "2.0-4.0m",
                    "color": "#4566fe"
                },
                {
                    "text": ">4.0m",
                    "color": "#1739ce"
                }
            ]

            colour_lookup = {}
            colour_lookup[0.1] = (255, 255, 255, 0)
            colour_lookup[0.5] = (206, 236, 254, 255)
            colour_lookup[1.0] = (156, 203, 254, 255)
            colour_lookup[2.0] = (114, 153, 254, 255)
            colour_lookup[4.0] = (69, 102, 254, 255)
            colour_lookup[9999999.0] = (23, 57, 206, 255)


        if server_path != None:
            # convert rainfall ASC data into geojson
            work_list = {'current': ['peak'], 'nowcast': ['peak'], 'forecast': ['1day', '2day', 'end']}



            for key, value in work_list.items():
                for item in value:
                    asc_file = unexecore.ascfile.ASCFile()
                    asc_file.load(flood_result[key][item])

                    name = key + '_' + item
                    label = item
                    if label == 'peak':
                        label = key

                    json_key = key

                    if json_key == 'forecast':
                        json_key = item

                    wdme_result['data'][label + '.geojson'] = asc_file.to_geojson(self.src_coords,
                                                                                  colourLookup=colour_lookup,
                                                                                  label='flood-map',
                                                                                  attrib_label='depth',
                                                                                  flip_coords=self.flip_coords)
                    wdme_result['result']['geojson'].append(
                        {'type': json_key, 'url': server_path + '/flooding/floodmodel/' + label + '.geojson'})

            # convert DEM model into greyscale
            name = 'dem'
            asc_file = unexecore.ascfile.ASCFile()
            asc_file.load(flood_result['caflood_src']['dem'])
            info = asc_file.get_histo()

            smallest = math.floor(min(info.keys()) - 1)
            largest = math.floor(max(info.keys()) + 1)

            num_range = largest - smallest

            grey_scale = {}
            steps = 32
            for i in range(steps):
                v = int((i * 255) / steps)
                grey_scale[smallest + ((i * num_range) / steps)] = (v, v, v, 255)

            grey_scale[asc_file.nodata] = (255, 255, 255, 0)

            wdme_result['data'][name + '.geojson'] = asc_file.to_geojson(self.src_coords, colourLookup=grey_scale,label=name,attrib_label='value', flip_coords=self.flip_coords)
            wdme_result['result']['geojson'].append(
                {'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

            # convert landuse into lookups
            name = 'land'
            asc_file = unexecore.ascfile.ASCFile()
            asc_file.load(flood_result['caflood_src'][name])
            info = asc_file.get_histo()

            grey_scale = {}
            steps = len(info.keys())

            i = 0
            for key, value in info.items():
                v = int((i * 255) / (steps + 1))
                grey_scale[key] = (v, v, v, 255)

                i += 1

            grey_scale[asc_file.nodata] = (255, 255, 255, 0)

            # add a bogus end of frame value to catch all the data
            v = int((steps * 255) / (steps + 1))
            grey_scale[9999] = (v, v, v, 0)

            wdme_result['data'][name + '.geojson'] = asc_file.to_geojson(self.src_coords, colourLookup=grey_scale,label=name,attrib_label='value', flip_coords=self.flip_coords)
            wdme_result['result']['geojson'].append(
                {'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

            # convert rain sensor regions into lookup
            name = 'rain'
            asc_file = unexecore.ascfile.ASCFile()
            asc_file.load(flood_result['caflood_src'][name])
            info = asc_file.get_histo()

            grey_scale = {}
            steps = len(info.keys())

            # qdd a bogus start vlaue for rain maps that only have 1 sensor
            first_val = sorted(info.keys())[0]
            first_val -= 1
            grey_scale[first_val] = (255, 255, 255, 0)

            i = 0
            for key, value in info.items():
                v = int((i * 255) / steps)
                grey_scale[key] = (v, v, v, 255)

                i += 1

            grey_scale[asc_file.nodata] = (255, 255, 255, 0)
            # add a bogus end of frame value to catch all the data
            v = int((steps * 255) / (steps + 1))
            grey_scale[9999] = (v, v, v, 0)

            wdme_result['data'][name + '.geojson'] = asc_file.to_geojson(self.src_coords, colourLookup=grey_scale,label=name,attrib_label='value', flip_coords=self.flip_coords)
            wdme_result['result']['geojson'].append(
                {'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

        if 'TrafficLights' in flood_result:
            wdme_result['result']['traffic_lights'] = flood_result['TrafficLights']
            wdme_result['result']['traffic_lights']["text"] = {
                "current": 'Not known at this time',
                "nowcast": 'Not known at this time',
                "forecast": 'Not known at this time'
            }

        traffic_lights = wdme_result['result']['traffic_lights']

        # hard-code traffic light results for demo
        if traffic_lights['current'] == 'green' and traffic_lights['nowcast'] == 'green' and traffic_lights[
            'forecast'] == 'green':
            traffic_lights['text'][
                'current'] = 'No to little rain observed over the past three days suggesting no real issues from flooding currently.'
            traffic_lights['text'][
                'nowcast'] = 'No rain forecast in the next couple of hours, suggesting no impact on current situation.'
            traffic_lights['text'][
                'forecast'] = 'No rain forecast in the next couple of days, suggesting no impact on current situation.'

        # high-tail
        if traffic_lights['current'] == 'amber' and traffic_lights['nowcast'] == 'amber' and traffic_lights[
            'forecast'] == 'red':
            traffic_lights['text'][
                'current'] = 'Some localised, but limited flooding in low-lying areas from recent rainfall over the last couple of days.'
            traffic_lights['text'][
                'nowcast'] = 'No rain forecast in the next couple of hours, suggesting that any residual water should continue receding.'
            traffic_lights['text'][
                'forecast'] = 'Significant rain forecast in next 2 to 3 days that could lead to increased flooding.'

        # forecast-short
        if traffic_lights['current'] == 'green' and traffic_lights['nowcast'] == 'red' and traffic_lights[
            'forecast'] == 'amber':
            traffic_lights['text'][
                'current'] = 'No to little rain observed over the past three days suggesting no real issues from flooding currently.'
            traffic_lights['text'][
                'nowcast'] = 'Significant rain forecast in the next couple of hours, leading to flooding'
            traffic_lights['text'][
                'forecast'] = 'No rain forecast in the next couple of days, which should reduce impact of flooding as flood waters recede.'

        # historic
        if traffic_lights['current'] == 'red' and traffic_lights['nowcast'] == 'amber' and traffic_lights[
            'forecast'] == 'green':
            traffic_lights['text'][
                'current'] = 'Recent rains have led to localised flooding, particularly in low-lying areas.'
            traffic_lights['text'][
                'nowcast'] = 'No rain forecast in the next couple of hours, suggesting that any residual water should continue receding.'
            traffic_lights['text'][
                'forecast'] = 'No rain forecast in the next couple of days, suggesting that any residual water should continue receding.'

        # extreme
        if traffic_lights['current'] == 'red' and traffic_lights['nowcast'] == 'red' and traffic_lights[
            'forecast'] == 'red':
            traffic_lights['text'][
                'current'] = 'Recent rains have led to significant flooding, particularly in low-lying areas.'
            traffic_lights['text'][
                'nowcast'] = 'Significant rain forecast in the next couple of hours, leading to increased flooding'
            traffic_lights['text'][
                'forecast'] = 'Less rain forecast in the next couple of days, suggesting that flooding should reduce over the coming days.'

        return wdme_result

    def create_empty_simulation_results(self) -> dict:
        result = {
            "TrafficLights": {
                "current": "test-1", "forecast": "test-3", "nowcast": "test-2"
            },
            "caflood_exe": "cafloodpro_GPU_64_2024",
            "caflood_src": {
                "dem":  self.output_filepath + "catchment_dem_8m.asc",
                "land": self.output_filepath + "catchment_landcover_8m.asc",
                "rain": self.output_filepath + "catchment_mask_8m.asc"
            },
            "current": {
                "caflood_response": 0,
                "peak": self.output_filepath + "current/current_WDrasterParam_PEAK.asc"
            },
            "forecast": {
                "caflood_response": 0,
                "1day": self.output_filepath + "forecast/forecast_WDrasterParam_86400.asc",
                "2day": self.output_filepath + "forecast/forecast_WDrasterParam_172800.asc",
                "end":  self.output_filepath + "forecast/forecast_WDrasterParam_252000.asc",
                "peak": self.output_filepath + "forecast/forecast_WDrasterParam_PEAK.asc"
            },
            "nowcast": {
                "caflood_response": 0,
                "peak": self.output_filepath +"nowcast/nowcast_WDrasterParam_PEAK.asc"
            },
            "timestamp": unexecore.time.datetime_to_fiware(datetime.datetime.now())
        }

        return result



def get_data_filename(filename: str) -> str:
    return os.path.dirname(__file__) + os.sep + 'data' + os.sep + filename
