import math
import os
import unexecore.file
import json
import flood_simulation.visualisation

def create_results(flood_result:dict, visualisation_path:str=None, server_path:str=None) -> dict:
    wdme_result = {
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
    }

    if visualisation_path != None and server_path != None:
        """
        make assets and put in folder
        """
        result_path = visualisation_path + os.sep

        if not os.path.exists(result_path):
            os.makedirs(result_path)
        else:
            unexecore.file.deltree(result_path)

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
                geojson = flood_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', 'flood-map', 'depth', colour_lookup)

                label = item
                if label == 'peak':
                    label = key

                json_key = key

                if json_key == 'forecast':
                    json_key = item

                with open(result_path + label + '.geojson', 'w') as f:
                    json.dump(geojson, f)

                wdme_result['geojson'].append({'type':json_key, 'url': server_path+'/flooding/floodmodel/'+ label+'.geojson'})

        # result['caflood_src']['dem'] -> greyscale
        name = 'dem'
        asc_file = unexecore.geofile.GeoFile()
        asc_file.loadASC(flood_result['caflood_src']['dem'])
        info = flood_simulation.visualisation.asc_get_info(asc_file)

        smallest = math.floor(min(info.keys())-1)
        largest = math.floor(max(info.keys())+1)

        num_range = largest - smallest

        #make a greyscale
        grey_scale = {}
        steps = 32
        for i in range(steps):
            v = int((i*255)/steps)
            grey_scale[smallest + ((i*num_range)/steps)] = (v,v,v,255)

        grey_scale[asc_file.nodata] = (255,255,255,0)

        im = asc_file.get_png(grey_scale)
        im.save(result_path + name + '.png')
        geojson = flood_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', name, 'value', grey_scale)

        with open(result_path + name + '.geojson', 'w') as f:
            json.dump(geojson, f)

        wdme_result['geojson'].append({'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

        # result['caflood_src']['land'] -> lookup
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

        im = asc_file.get_png(grey_scale)
        im.save(result_path + name + '.png')
        geojson = flood_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', name, 'value', grey_scale)

        with open(result_path + name + '.geojson', 'w') as f:
            json.dump(geojson, f)

        wdme_result['geojson'].append({'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

        # result['caflood_src']['rain'] -> lookup
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

        im = asc_file.get_png(grey_scale)
        im.save(result_path + name + '.png')
        geojson = flood_simulation.visualisation.asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', name, 'value', grey_scale)

        with open(result_path + name + '.geojson', 'w') as f:
            json.dump(geojson, f)

        wdme_result['geojson'].append({'type': name, 'url': server_path + '/flooding/floodmodel/' + name + '.geojson'})

    if 'TrafficLights' in flood_result:
        wdme_result['traffic_lights'] = flood_result['TrafficLights']
        wdme_result['traffic_lights']["text"] = {
            "current": 'Not known at this time',
            "nowcast": 'Not known at this time',
            "forecast": 'Not known at this time'
        }

    #hard-code traffic light results for demo
    if wdme_result['traffic_lights']['current'] == 'green' and wdme_result['traffic_lights']['nowcast'] == 'green' and wdme_result['traffic_lights']['forecast'] == 'green':
        wdme_result['traffic_lights']['text']['current'] = 'No to little rain observed over the past three days suggesting no real issues from flooding currently.'
        wdme_result['traffic_lights']['text']['nowcast'] = 'No rain forecast in the next couple of hours, suggesting no impact on current situation.'
        wdme_result['traffic_lights']['text']['forecast'] = 'No rain forecast in the next couple of days, suggesting no impact on current situation.'

    # high-tail
    if wdme_result['traffic_lights']['current'] == 'amber' and wdme_result['traffic_lights']['nowcast'] == 'amber' and wdme_result['traffic_lights']['forecast'] == 'red':
        wdme_result['traffic_lights']['text']['current'] = 'Some localised, but limited flooding in low-lying areas from recent rainfall over the last couple of days.'
        wdme_result['traffic_lights']['text']['nowcast'] = 'No rain forecast in the next couple of hours, suggesting that any residual water should continue receding.'
        wdme_result['traffic_lights']['text']['forecast'] = 'Significant rain forecast in next 2 to 3 days that could lead to increased flooding.'

    # forecast-short
    if wdme_result['traffic_lights']['current'] == 'green' and wdme_result['traffic_lights']['nowcast'] == 'red' and wdme_result['traffic_lights']['forecast'] == 'amber':
        wdme_result['traffic_lights']['text']['current'] = 'No to little rain observed over the past three days suggesting no real issues from flooding currently.'
        wdme_result['traffic_lights']['text']['nowcast'] = 'Significant rain forecast in the next couple of hours, leading to flooding'
        wdme_result['traffic_lights']['text']['forecast'] = 'No rain forecast in the next couple of days, which should reduce impact of flooding as flood waters recede.'

    # historic
    if wdme_result['traffic_lights']['current'] == 'red' and wdme_result['traffic_lights']['nowcast'] == 'amber' and wdme_result['traffic_lights']['forecast'] == 'green':
        wdme_result['traffic_lights']['text']['current'] = 'Recent rains have led to localised flooding, particularly in low-lying areas.'
        wdme_result['traffic_lights']['text']['nowcast'] = 'No rain forecast in the next couple of hours, suggesting that any residual water should continue receding.'
        wdme_result['traffic_lights']['text']['forecast'] = 'No rain forecast in the next couple of days, suggesting that any residual water should continue receding.'

    # extreme
    if wdme_result['traffic_lights']['current'] == 'red' and wdme_result['traffic_lights']['nowcast'] == 'red' and wdme_result['traffic_lights']['forecast'] == 'red':
        wdme_result['traffic_lights']['text']['current'] = 'Recent rains have led to significant flooding, particularly in low-lying areas.'
        wdme_result['traffic_lights']['text']['nowcast'] = 'Significant rain forecast in the next couple of hours, leading to increased flooding'
        wdme_result['traffic_lights']['text']['forecast'] = 'Less rain forecast in the next couple of days, suggesting that flooding should reduce over the coming days.'

    return wdme_result