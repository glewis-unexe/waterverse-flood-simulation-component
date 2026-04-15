import unexecore.ascfile

def asc_get_info(asc_file: unexecore.ascfile.ASCFile) -> dict:
    info = {}
    try:
        for y in range(0, asc_file.nrows):
            for x in range(0, asc_file.ncols):
                try:
                    v0 = asc_file.data[y][x]

                    if v0 != asc_file.nodata:
                        if v0 not in info:
                            info[v0] = 0
                        info[v0] += 1

                except Exception as e:
                    print(unexecore.debug.exception_to_string(e))
    except Exception as e:
        print(unexecore.debug.exception_to_string(e))

    return info

if False:
    filename = '/home/gareth/Documents/dev/work/waterverse/for-forking/waterverse-flood-simulation-component/flood_simulation/output/current/current_WDrasterParam_PEAK.asc'
    #filename = '/home/gareth/Documents/dev/work/waterverse/for-forking/waterverse-flood-simulation-component/wdme_flood_component/sim_output/current/current_WDrasterParam_PEAK.asc'
    asc_file = unexecore.ascfile.ASCFile()
    asc_file.load(filename)
    info = asc_get_info(asc_file)

    print()


import requests
import json
import os
request_url = 'http://api.weatherapi.com/v1/history.json?key=f32e4b0e08d94389a4b132529231104&q=50.55, -3.99&dt=2026-03-10'

request_url = 'http://api.weatherapi.com/v1/history.json?key=' + os.environ['WEATHERAPI_KEY'] + '&q='
request_url += '50.55, -3.99'
request_url += '&dt=' + '2026-03-08'
request_url += '&end_dt=' + '2026-03-14'
request_url += '&aqi=' + 'no'
request_url += '&alerts=' + 'no'

rainlist = {}
r = requests.get(request_url)


if r.status_code == 200:
    weather_data = json.loads(r.text)
    for day in weather_data['forecast']['forecastday']:
        for hour in day['hour']:
            rainlist[hour['time']+':00Z'] = hour['precip_mm']

print()

