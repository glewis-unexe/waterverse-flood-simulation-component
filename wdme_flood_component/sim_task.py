import copy
import queue
import threading
import datetime
import time
import os
import flood_simulation
import json
import unexecore.debug
import unexecore.file


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


    def add_work(self, data: dict, url_root:str, timestamp: datetime.datetime) -> None:
        self.work_queue.append({'data': data, 'timestamp': timestamp, 'url_root': url_root})

    def run(self):
        while self.running:
            if len(self.work_queue) > 0:
                try:
                    print('Running Task')
                    item = self.work_queue.pop(0)

                    output_filepath = os.getcwd() + os.sep + 'sim_output'
                    model = flood_simulation.rainfall_model.Model(output_filepath=output_filepath)
                    result = model.run(item['data'], timestamp=item['timestamp'])
                    new_result = flood_simulation.wdme_results.create_results(result, item['url_root'])

                    print('Running Task - Finished')

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

            time.sleep(1)


task = SimTask()
task.start()

