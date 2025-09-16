import datetime
import os
import json

import unexecore.debug

from fastapi import FastAPI

import etteln_rain_simulation.rainfall_model
import etteln_rain_simulation.visualisation

app = FastAPI()



@app.get("/flooding/floodimage/{filename}")
async def get_flood_image(filename):
    return {"message": "Hello World"}

@app.get("/flooding/floodmodel/{filename}")
async def get_flood_model(filename):
    return {"message": "Hello World"}

@app.get("/flooding/get_flood_data")
async def get_flood_data():
    return {"message": "Hello World"}

@app.get("/flooding/get_flood_json")
async def get_flood_json():
    return {"message": "Hello World"}


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
async def post_flood_data(item: Item):
    output_filepath = os.getcwd() + os.sep + 'sim_output'
    model = etteln_rain_simulation.rainfall_model.Model(output_filepath=output_filepath)

    try:
        colour_lookup = {}
        colour_lookup[0.1] = (255, 255, 255, 0)
        colour_lookup[0.5] = (206, 236, 254, 255)
        colour_lookup[1.0] = (156, 203, 254, 255)
        colour_lookup[2.0] = (114, 153, 254, 255)
        colour_lookup[4.0] = (69, 102, 254, 255)
        colour_lookup[9999999.0] = (23, 57, 206, 255)

        result = model.run(item.model_dump(), timestamp=datetime.datetime.now(datetime.timezone.utc))

        work_list = {'current':['peak'], 'nowcast':['peak'], 'forecast':['peak','1day','2day','end']}

        result_path = output_filepath + os.sep + 'vis_outputs' + os.sep
        os.makedirs(result_path)

        for key, value in work_list.items():

            for item in value:
                asc_file = unexecore.geofile.GeoFile()
                asc_file.loadASC(result[key][item])

                name = key +'_'+item

                im = asc_file.get_png(colour_lookup)
                im.save(result_path + name + '.png')

                geojson = etteln_rain_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', colour_lookup)
                with open(result_path + name + '.geojson', 'w') as f:
                    json.dump(geojson, f)

        #result['caflood_src']['dem'] -> greyscale
        #result['caflood_src']['land'] -> lookup
        # result['caflood_src']['rain'] -> lookup

    except Exception as e:
        print(unexecore.debug.exception_to_string(e))

    return {"message": "Hello World"}