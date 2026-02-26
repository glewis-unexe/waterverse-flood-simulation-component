from fastapi import APIRouter
from fastapi import FastAPI, Response, Request

import waterverse_sdg.sdg as sdg
import unexecore.time
import unexecore.debug
import datetime
import json
import os

import sim_task

pilot = 'etteln'
start_date = unexecore.time.datetime_to_fiware(datetime.datetime.now(datetime.timezone.utc).replace(minute=0, hour=0, second=0, microsecond=0))
datapath = sdg.get_datapath() + os.sep

sdg.add_pilot(pilot)

sdg.add_sensor_to_pilot(pilot, 'test', json.load(open(datapath + 'etteln_payload.json')))
sdg.reset_pilot(pilot, start_date)

router = APIRouter()

@router.put("/run_scenario/{scenario_name}")
def put_scenario(scenario_name:str, request: Request, response: Response):
    print(scenario_name)
    try:
        sdg.set_current_state(pilot, 'test', {"mode": scenario_name})
        data = sdg.get_data(pilot, 'test', 1)[0]

        sim_task.task.add_work(data, request.url.scheme + '://' + request.url.netloc, timestamp=datetime.datetime.now(datetime.timezone.utc))

        response.status_code = 200
    except Exception as e:
        print(unexecore.debug.exception_to_string(e))
        response.status_code = 500

@router.get("/get_scenarios")
def get_scenario(response: Response):
    response.status_code = 200

    result = []
    try:
        for scenario in sdg.pilot_model[pilot]['test']['config']['attributes'][0]['range']:
            result.append({'id': scenario['name'], 'print_name': scenario['name']})
    except Exception as e:
        print(unexecore.debug.exception_to_string(e))
        response.status_code = 500

    return result
