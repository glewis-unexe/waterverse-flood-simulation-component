"""
load EA princetown dataset from csv file
 - put into a day / hour format

load weatherapi data for princetown
- put into dict of:
    TOD: EA_datapoint, WAPI_datapoint
"""

import csv
import unexecore.time

rainlist = {}

with open("Princetown-rainfall-data.csv", "r") as f:
    reader = csv.reader(f, delimiter=",")
    for i, line in enumerate(reader):
        if i > 0:
            time = unexecore.time.fiware_to_datetime(line[0])

            hour_stamp = str(time.year) + '-' + str(time.month).zfill(2) + '-' + str(time.day).zfill(2) + ' ' + str(time.hour).zfill(2) + ':' + '00'

            if hour_stamp not in rainlist:
                rainlist[hour_stamp] = {'EA':0, 'WAPI':-1}

            rainlist[hour_stamp]['EA'] += float(line[1])

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

r = requests.get(request_url)

if r.status_code == 200:
    weather_data = json.loads(r.text)
    for day in weather_data['forecast']['forecastday']:
        for hour in day['hour']:

            time = hour['time']

            if hour['time'] in rainlist:
                rainlist[hour['time']]['WAPI'] = hour['precip_mm']

ea = 0
wapi = 0
for key in rainlist:
    ea += rainlist[key]['EA']
    wapi += rainlist[key]['WAPI']

    print(key +',' + str(rainlist[key]['EA'])+',' + str(rainlist[key]['WAPI']))

print()
