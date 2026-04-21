import datetime
import os
import json

import unexecore.debug
import flood_thread

#flood_service = flood_thread.ThreadedService()

import flood_viewer
#flood_service = flood_viewer.FloodViewer('/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/etteln/200/output_data.json')
flood_service = flood_viewer.FloodViewer('/home/gareth/Documents/local/waterverse-flood-simulation-component/wdme_flood_component/sim_output/torbay/400/output_data.json')
flood_service.init()

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

app = FastAPI(title='Flooding WDME Component', swagger_ui_parameters={"defaultModelsExpandDepth": -1})

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/flooding/floodmodel/{filename}")
def get_flood_model(filename, response: Response):
    try:
        result = flood_service.get_flood_model(filename)

        if(len(result) > 0):
            return result

    except Exception as e:
        response.status = 500
        return {unexecore.debug.exception_to_string(e)}

    response.status = 404
    return {'No record for: ' + filename}

@app.get("/flooding/get_flood_data")
def get_flood_data():
    return flood_service.get_current_results()


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
def post_flood_data(item: Item, request:Request, response: Response):


    try:
        flood_service.add_data(item.model_dump(), timestamp=datetime.datetime.now(datetime.timezone.utc), url=request.url.scheme + '://' + request.url.netloc)
        return flood_service.get_current_results()

    except Exception as e:
        print(unexecore.debug.exception_to_string(e))
        response.status_code = 500

    return {}


@app.get("/", include_in_schema=False)
def read_root():
    return FileResponse(os.getcwd() + os.sep + 'static' + os.sep + 'index.html')

