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

class TorbayModel (unexe_flood_simulation.weatherapi_model.Weatherapi_Model):
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
                '1': rainfall_data,
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

if __name__ == '__main__':
    t0 = time.time()

    try:
        output_filepath = os.getcwd()+os.sep+'output'+os.sep
        unexecore.file.buildfilepath(output_filepath)
        model = TorbayModel(output_filepath=output_filepath)
        result = model.run(datetime.datetime.now(datetime.timezone.utc),asc_scale=500)
        wdme_results = unexe_flood_simulation.wdme_results.create_results(result,source_coords='EPSG:27700', flip_coords=True, server_path='http://whatever.com')

        for item in wdme_results['data']:
            with open(output_filepath + item, "w") as f:
                json.dump(wdme_results['data'][item], f, indent=4)

    except Exception as e:
        print(unexecore.debug.exception_to_string(e))

    print('Load:' + str(round(time.time() - t0, 2)))
