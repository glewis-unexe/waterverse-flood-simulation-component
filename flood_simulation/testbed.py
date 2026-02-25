import os
import datetime

import unexecore.testharness
import unexecore.debug

import flood_simulation.rainfall_model
import flood_simulation.wdme_results

import json
import requests

import waterverse_sdg.sdg as sdg


class etteln_Harness(unexecore.testharness.TestHarness):
    def __init__(self):
        super().__init__()

        option_id = 1

        self.wdme_flood_component_url = 'http://127.0.0.1:9999'
        self.wdme_flood_component_url = 'http://192.168.68.111:52000/'


        self.output_filepath = os.getcwd() + os.sep + 'output' + os.sep
        self.model = flood_simulation.rainfall_model.Model(output_filepath=self.output_filepath)

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

            for scenario in sdg.pilot_model[self.pilot]['test']['config']['attributes'][0]['range']:
                self.options[str(option_id)] = {'label': 'Call WDME Component Scenario: ' + scenario['name'], 'function': self.call_wdme_flood_component, 'args': {'scenario': scenario['name']}}
                option_id += 1


        except Exception as e:
            self.log('SDG: Failed to start-up ' + self.pilot + ' ' + unexecore.debug.exception_to_string(e))



    def log(self, text):
        print(text)

    def std_model(self, args:dict):
        try:

            sdg.set_current_state(self.pilot, 'test', {"mode": args['scenario']})

            data = sdg.get_data(self.pilot, 'test', 1)

            result = self.model.run(data[0], timestamp=datetime.datetime.now(datetime.timezone.utc))
            wdme_results = flood_simulation.wdme_results.create_results(result,'http://whatever.com')
            print(json.dumps(wdme_results, indent=4))
            for item in wdme_results['data']:
                with open('output' +os.sep + item, "w") as f:
                    json.dump(wdme_results['data'][item], f, indent=4)

        except Exception as e:
            self.log(unexecore.debug.exception_to_string(e))

    def call_wdme_flood_component(self, args:dict):
        try:

            sdg.set_current_state(self.pilot, 'test', {"mode": args['scenario']})

            data = sdg.get_data(self.pilot, 'test', 1)

            r = requests.post(self.wdme_flood_component_url + '/flooding/post_flood_data',json = data[0])

            if r.ok:
                print('ok: ' + json.dumps(json.loads(r.text), indent=4) )
            else:
                print('error: ' + str(r.status_code) )

        except Exception as e:
            self.log(unexecore.debug.exception_to_string(e))


if __name__ == '__main__':
    harness = etteln_Harness()
    harness.run()