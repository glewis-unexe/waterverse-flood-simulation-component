import threading
import datetime
import time
import os
import inspect
from copy import deepcopy

import unexecore.logger
import unexecore.time

import flood_simulation

module='FLOOD-THREAD'

class djangolike_logger(unexecore.logger.Logger):
    def __init__(self):
        self.data = []

    def log(self, text:str, level:str = 'INFO', module:str='n/a'):
        print( unexecore.time.datetime_to_fiware(datetime.datetime.now()) +' ' + level +':' + text)

        if len(self.data) > 100:
            self.data.pop(len(self.data)-1)

    def exception(self, exception, cf, module:str='n/a'):
        try:
            text = self.exception_to_string(exception)
            self.log(self.formatmsg(cf, text), level='ERROR', module=module)
        except Exception as e:
            self.fail(cf, 'Failed to process exception!')


    def get_data(self):
        return self.data

    def current_frame(self, cf:inspect.currentframe):
        return unexecore.logger.formatmsg(cf, '')


class ThreadedService:

    def __init__(self, logger=None):
        self.thread = None
        self.is_running = False

        self.work_queue = []
        self.current_results = {}

        self.lock = threading.Lock()

        self.logger = logger

        if self.logger == None:
            self.logger = djangolike_logger()

        self.normal_sleep_seconds = 10# * 60
        self.quick_sleep_seconds = 30
        self.last_collection_time = None
        self.last_big_task_time = None
        self.big_task_time_seconds = 2 * 60

        if 'IOT_NORMAL_SLEEP_AS_MINUTES' in os.environ:
            self.normal_sleep_seconds = float(os.environ['IOT_NORMAL_SLEEP_AS_MINUTES']) * 60

        if 'IOT_QUICK_SLEEP_AS_MINUTES' in os.environ:
            self.quick_sleep_seconds = float(os.environ['IOT_QUICK_SLEEP_AS_MINUTES']) * 60

        if 'IOT_BIG_TASK_AS_MINUTES' in os.environ:
            self.big_task_time_seconds = float(os.environ['IOT_BIG_TASK_AS_MINUTES']) * 60

        self.logger.log(
            'IOT_NORMAL_SLEEP:' + str(self.normal_sleep_seconds) + 's ' + str(self.normal_sleep_seconds / 60) + 'min',
            module=module)
        self.logger.log(
            'IOT_QUICK_SLEEP:' + str(self.quick_sleep_seconds) + 's ' + str(self.quick_sleep_seconds / 60) + 'min',
            module=module)
        self.logger.log(
            'IOT_BIG_TASK:' + str(self.big_task_time_seconds) + 's ' + str(self.big_task_time_seconds / 60) + 'min',
            module=module)

    def init(self):


        self.thread = threading.Thread(target=self.run_threaded_service)
        self.thread.start()

    def run_threaded_service(self):
        sleep_time = 0
        self.is_running = True

        while self.is_running:
            try:
                current_time = datetime.datetime.now()

                if self.last_collection_time is None or (current_time - self.last_collection_time).total_seconds() >= sleep_time:

                    if len(self.work_queue) > 0:
                        self.logger.log('Start flooding sim', level='INFO', module=module)

                        work_item = self.work_queue.pop(0)

                        output_filepath = os.getcwd() + os.sep + 'sim_output'
                        model = flood_simulation.rainfall_model.Model(output_filepath=output_filepath)
                        result = model.run(work_item['data'], timestamp=work_item['timestamp'])

                        current_results = flood_simulation.wdme_results.create_results(result,work_item['url'])

                        with self.lock:
                            self.current_results = deepcopy(current_results)

                        #success
                        self.last_collection_time = current_time
                        self.logger.log('Collected background data', level='INFO', module=module)

                    sleep_time = self.normal_sleep_seconds
                    time.sleep(sleep_time)

            except Exception as e:
                sleep_time = self.quick_sleep_seconds
                self.logger.exception(e, module=module)

    def add_data(self, data:dict, timestamp:datetime.datetime, url:str):
        self.work_queue.append({'data':data, 'timestamp':timestamp, 'url':url})

        self.logger.log('Add data', level='INFO', module=module)

    def get_current_results(self) -> dict:
        result = {}
        with self.lock:
            if 'result' in self.current_results:
                result = self.current_results['result'].copy()

        return result

    def get_flood_model(self,filename:str):
        result = {}
        with self.lock:
            if filename in self.current_results['data']:
                result = self.current_results['data'][filename].copy()

        return result
