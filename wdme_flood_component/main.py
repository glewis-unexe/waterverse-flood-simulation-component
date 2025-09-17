import datetime
import os
import json

import unexecore.debug

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

origins = [
    "http://localhost",
    "http://localhost:63342",
]


from fastapi.staticfiles import StaticFiles


import flood_simulation.rainfall_model
import flood_simulation.wdme_results
from starlette.requests import Request

current_results = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/flooding/floodmodel/{filename}")
async def get_flood_model(filename, response: Response):
    try:
        global current_results
        if filename in current_results['data']:
            return current_results['data'][filename]

    except Exception as e:
        response.status = 500
        return {unexecore.debug.exception_to_string(e)}

    response.status = 404
    return {'No record for: ' + filename}

@app.get("/flooding/get_flood_data")
async def get_flood_data():
    global current_results

    if 'result' in current_results:
        return current_results['result']

    return {}


from pydantic import BaseModel


class TrafficLights(BaseModel):
    current: str
    nowcast: str
    forecast: str

class Item(BaseModel):
    Last72Hour: float
    Last24Hour: float
    Last12Hour: float
    Last4Hour: float
    Last2Hour: float
    LastHour: float
    Forecast2Hour: float
    Forecast0To24: float
    Forecast24To48: float
    Forecast48To72: float
    TrafficLights: TrafficLights
    dateObserved: str

@app.post("/flooding/post_flood_data")
async def post_flood_data(item: Item, request:Request, response: Response):

    output_filepath = os.getcwd() + os.sep + 'sim_output'
    model = flood_simulation.rainfall_model.Model(output_filepath=output_filepath)

    try:
        result = model.run(item.model_dump(), timestamp=datetime.datetime.now(datetime.timezone.utc))

        global current_results
        current_results = flood_simulation.wdme_results.create_results(result, request.url.scheme +'://'+request.url.netloc)

        return current_results['result']

    except Exception as e:
        print(unexecore.debug.exception_to_string(e))
        response.status_code = 500

    return {}


@app.get("/")
def read_root():
    return FileResponse(os.getcwd() + os.sep + 'static' + os.sep + 'index.html')

