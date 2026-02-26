from fastapi import APIRouter
from fastapi import FastAPI, Response, Request

import datetime
import sim_task

import unexecore.debug
from fastapi.templating import Jinja2Templates


router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/flooding/floodmodel/{filename}")
def get_flood_model(filename, response: Response):
    try:

        result =  sim_task.task.get_current_data()

        if 'data' in result and  filename in result['data']:
            response.status = 200
            return result['data'][filename]

        response.status = 404
        return {'No record for: ' + filename}

    except Exception as e:
        response.status = 500
        return {unexecore.debug.exception_to_string(e)}


@router.get("/flooding/get_flood_data")
def get_flood_data(response: Response):
    try:
        response.status = 200
        result = sim_task.task.get_current_data()
        return result['result']
    except Exception as e:
        response.status = 500
        return {unexecore.debug.exception_to_string(e)}


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

@router.post("/flooding/post_flood_data")
def post_flood_data(item: Item, request:Request, response: Response):
    try:
        sim_task.task.add_work(item.model_dump(), request.url.scheme +'://'+request.url.netloc, timestamp=datetime.datetime.now(datetime.timezone.utc))

        return sim_task.task.get_current_data()
    except Exception as e:
        print(unexecore.debug.exception_to_string(e))
        response.status_code = 500

    return {}
