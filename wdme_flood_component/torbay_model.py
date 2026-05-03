import os
import inspect

import unexecore.logger
import unexecore.debug

import etteln_model
class TorbayModel(etteln_model.EttelnModel):
    def __init__(self, output_filepath: str=None, delete_files:bool=False):
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
