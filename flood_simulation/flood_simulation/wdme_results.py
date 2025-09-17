import math
import os
import unexecore.file
import json
import flood_simulation.visualisation

def create_results(flood_result:dict, server_path:str=None) -> dict:
    wdme_result = {
        #results to return to user
        'result':
        {
            "timestamp": flood_result["timestamp"],
            "traffic_lights": {
                "current": "<set>",
                "nowcast": "<set>",
                "forecast": "<set>",
                "text": {
                    "current": 'Not known at this time',
                    "nowcast": 'Not known at this time',
                    "forecast": 'Not known at this time'
                }
            },
            "color_key": [
                {
                    "text": "<0.1m",
                    "color": "#ffffff"
                },
                {
                    "text": "0.1-0.3m",
                    "color": "#ff8c00"
                },
                {
                    "text": ">0.3m",
                    "color": "#ff1414"
                }
            ],
            "geojson": []
        },
        #data to return through API call
        'data':{
        }
    }

    #this should be the blue scale that is normally used
    wdme_result['result']['color_key'] = [
        {
            "text": "<0.1m",
            "color": "#ffffff"
        },
        {
            "text": "0.1-0.5m",
            "color": "#ceecfe"
        },
        {
            "text": "0.5-1.0m",
            "color": "#9ccbfe"
        },
        {
            "text": "1.0-2.0m",
            "color": "#7299fe"
        },
        {
            "text": "2.0-4.0m",
            "color": "#4566fe"
        },
        {
            "text": ">4.0m",
            "color": "#1739ce"
        }
    ]

    if server_path != None:
        #convert rainfall ASC data into geojson
        work_list = {'current': ['peak'], 'nowcast': ['peak'], 'forecast': ['1day', '2day', 'end']}

        colour_lookup = {}
        colour_lookup[0.1] = (255, 255, 255, 0)
        colour_lookup[0.5] = (206, 236, 254, 255)
        colour_lookup[1.0] = (156, 203, 254, 255)
        colour_lookup[2.0] = (114, 153, 254, 255)
        colour_lookup[4.0] = (69, 102, 254, 255)
        colour_lookup[9999999.0] = (23, 57, 206, 255)

        for key, value in work_list.items():
            for item in value:
                asc_file = unexecore.geofile.GeoFile()
                asc_file.loadASC(flood_result[key][item])

                name = key + '_' + item
                label = item
                if label == 'peak':
                    label = key

                json_key = key

                if json_key == 'forecast':
                    json_key = item

                wdme_result['data'][label+'.geojson'] = flood_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', 'flood-map', 'depth', colour_lookup)
                wdme_result['result']['geojson'].append({'type':json_key, 'url': server_path+'/flooding/floodmodel/'+ label+'.geojson'})

        # convert DEM model into greyscale
        name = 'dem'
        asc_file = unexecore.geofile.GeoFile()
        asc_file.loadASC(flood_result['caflood_src']['dem'])
        info = flood_simulation.visualisation.asc_get_info(asc_file)

        smallest = math.floor(min(info.keys())-1)
        largest = math.floor(max(info.keys())+1)

        num_range = largest - smallest

        grey_scale = {}
        steps = 32
        for i in range(steps):
            v = int((i*255)/steps)
            grey_scale[smallest + ((i*num_range)/steps)] = (v,v,v,255)

        grey_scale[asc_file.nodata] = (255,255,255,0)

        wdme_result['data'][name + '.geojson'] = flood_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', name, 'value', grey_scale)
        wdme_result['result']['geojson'].append({'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

        # convert landuse into lookups
        name = 'land'
        asc_file = unexecore.geofile.GeoFile()
        asc_file.loadASC(flood_result['caflood_src'][name])
        info = flood_simulation.visualisation.asc_get_info(asc_file)

        grey_scale = {}
        steps = len(info.keys())

        i = 0
        for key, value in info.items():
            v = int((i * 255) / steps)
            grey_scale[key] = (v, v, v, 255)

            i += 1

        grey_scale[asc_file.nodata] = (255, 255, 255, 0)

        wdme_result['data'][name + '.geojson'] = flood_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', name, 'value', grey_scale)
        wdme_result['result']['geojson'].append({'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

        # convert rain sensor regions into lookup
        name = 'rain'
        asc_file = unexecore.geofile.GeoFile()
        asc_file.loadASC(flood_result['caflood_src'][name])
        info = flood_simulation.visualisation.asc_get_info(asc_file)

        grey_scale = {}
        steps = len(info.keys())

        i = 0
        for key, value in info.items():
            v = int((i * 255) / steps)
            grey_scale[key] = (v, v, v, 255)

            i+=1

        grey_scale[asc_file.nodata] = (255, 255, 255, 0)

        wdme_result['data'][name + '.geojson'] = flood_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', name, 'value', grey_scale)
        wdme_result['result']['geojson'].append({'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

    if 'TrafficLights' in flood_result:
        wdme_result['result']['traffic_lights'] = flood_result['TrafficLights']
        wdme_result['result']['traffic_lights']["text"] = {
            "current": 'Not known at this time',
            "nowcast": 'Not known at this time',
            "forecast": 'Not known at this time'
        }

    traffic_lights = wdme_result['result']['traffic_lights']

    #hard-code traffic light results for demo
    if traffic_lights['current'] == 'green' and traffic_lights['nowcast'] == 'green' and traffic_lights['forecast'] == 'green':
        traffic_lights['text']['current'] = 'No to little rain observed over the past three days suggesting no real issues from flooding currently.'
        traffic_lights['text']['nowcast'] = 'No rain forecast in the next couple of hours, suggesting no impact on current situation.'
        traffic_lights['text']['forecast'] = 'No rain forecast in the next couple of days, suggesting no impact on current situation.'

    # high-tail
    if traffic_lights['current'] == 'amber' and traffic_lights['nowcast'] == 'amber' and traffic_lights['forecast'] == 'red':
        traffic_lights['text']['current'] = 'Some localised, but limited flooding in low-lying areas from recent rainfall over the last couple of days.'
        traffic_lights['text']['nowcast'] = 'No rain forecast in the next couple of hours, suggesting that any residual water should continue receding.'
        traffic_lights['text']['forecast'] = 'Significant rain forecast in next 2 to 3 days that could lead to increased flooding.'

    # forecast-short
    if traffic_lights['current'] == 'green' and traffic_lights['nowcast'] == 'red' and traffic_lights['forecast'] == 'amber':
        traffic_lights['text']['current'] = 'No to little rain observed over the past three days suggesting no real issues from flooding currently.'
        traffic_lights['text']['nowcast'] = 'Significant rain forecast in the next couple of hours, leading to flooding'
        traffic_lights['text']['forecast'] = 'No rain forecast in the next couple of days, which should reduce impact of flooding as flood waters recede.'

    # historic
    if traffic_lights['current'] == 'red' and traffic_lights['nowcast'] == 'amber' and traffic_lights['forecast'] == 'green':
        traffic_lights['text']['current'] = 'Recent rains have led to localised flooding, particularly in low-lying areas.'
        traffic_lights['text']['nowcast'] = 'No rain forecast in the next couple of hours, suggesting that any residual water should continue receding.'
        traffic_lights['text']['forecast'] = 'No rain forecast in the next couple of days, suggesting that any residual water should continue receding.'

    # extreme
    if traffic_lights['current'] == 'red' and traffic_lights['nowcast'] == 'red' and traffic_lights['forecast'] == 'red':
        traffic_lights['text']['current'] = 'Recent rains have led to significant flooding, particularly in low-lying areas.'
        traffic_lights['text']['nowcast'] = 'Significant rain forecast in the next couple of hours, leading to increased flooding'
        traffic_lights['text']['forecast'] = 'Less rain forecast in the next couple of days, suggesting that flooding should reduce over the coming days.'

    return wdme_result