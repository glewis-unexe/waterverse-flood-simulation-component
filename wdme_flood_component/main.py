import datetime
import os
import json

import unexecore.debug
import sim_task

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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

import scenarios
import flooding
app.include_router(scenarios.router)
app.include_router(flooding.router)

templates = Jinja2Templates(directory="templates")

@app.get("/", include_in_schema=False, response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"id": os.environ['MAPBOX_ID']}
    )

@app.get("/testbed", include_in_schema=False, response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="testbed.html"
    )
