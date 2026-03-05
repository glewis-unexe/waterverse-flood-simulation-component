import copy
import threading
import datetime
import time
import os
import unexe_flood_simulation.wdme_results
import unexe_flood_simulation.weatherapi_model
import json
import unexecore.debug
import unexecore.file
import unexecore.time


class SimTask(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.work_queue = []
        self.running = False
        self.current_results = {'result':{'traffic_lights': {'current': 'grey','nowcast': 'grey','forecast': 'grey'}},
                                "color_key": [],
                                'geojson': []
                               }
        self.lock = False
        self.thread = threading.Thread(target=self.run, args=())


    def get_current_data(self) -> dict:
        result = {}
        try:
            print('Get Data')
            while self.lock:
                time.sleep(0.01)

            self.lock = True
            result = self.current_results
            self.lock = False
            print('Get Data - Got')
        except Exception as e:
            self.lock = False
            print('Get Data - Failed')

        return result

    def start(self):
        self.running = True
        self.lock = False
        self.thread.start()


    def run(self):
        while self.running:
            try:
                print('Running Task')
                t0 = time.time()
                output_filepath = os.getcwd() + os.sep + 'sim_output'
                model = unexe_flood_simulation.weatherapi_model.Weatherapi_Model(output_filepath=output_filepath)
                result = model.run(datetime.datetime.now(datetime.timezone.utc),asc_scale=75)
                new_result = unexe_flood_simulation.wdme_results.create_results(result, os.environ['APP_URL'])

                timestamp = unexecore.time.fiware_to_datetime(new_result['result']['timestamp'])

                new_result['result']['TOS'] = str(timestamp.year) +'-'+ str(timestamp.month).zfill(2) + '-'+str(timestamp.day).zfill(2) +' ' + str(timestamp.hour).zfill(2) +':' +'00'

                print('Running Task - Finished:' + str(round(time.time() - t0, 2)))

                while self.lock:
                    time.sleep(0.01)

                self.lock = True
                self.current_results = copy.deepcopy(new_result)
                self.lock = False

                for item in new_result['data']:
                    path = os.getcwd() + os.sep + 'output' + os.sep
                    unexecore.file.buildfilepath(path)
                    with open(path + item, "w") as f:
                        json.dump(new_result['data'][item], f, indent=4)

                print('Running Task - Written Results')
            except Exception as e:
                print(unexecore.debug.exception_to_string(e))
                print('Running Task - Failed')
                self.lock = False

            time.sleep(5*60)
task = SimTask()
task.start()

