import os
import json
import requests
import unexecore.time
import datetime

duration_in_days = 3

loc = '51.63, 8.76'

current_date = datetime.datetime.now(datetime.timezone.utc)
date = unexecore.time.datetime_to_date(current_date - datetime.timedelta(days=duration_in_days))

#hist

rainlist = {}

weatherapi_now_time = str(current_date.year) +'-'+ str(current_date.month).zfill(2) + '-'+str(current_date.day).zfill(2) +' ' + str(current_date.hour).zfill(2) +':' +'00'

request_url = 'http://api.weatherapi.com/v1/history.json?key=' +os.environ['WEATHERAPI_KEY']+ '&q='
request_url += loc
request_url += '&dt=' + date
request_url += '&end_dt=' + unexecore.time.datetime_to_date(current_date)
request_url += '&aqi=' + 'no'
request_url += '&alerts=' + 'no'

r = requests.get(request_url)

if r.status_code == 200:

    weather_data = json.loads(r.text)
    for day in weather_data['forecast']['forecastday']:
        for hour in day['hour']:
            if hour['time'] < weatherapi_now_time:
                rainlist[hour['time']] = hour['precip_mm']

#forecast
request_url = 'http://api.weatherapi.com/v1/forecast.json?key=' +os.environ['WEATHERAPI_KEY']+ '&q='
request_url += loc
request_url += '&days=' + str(duration_in_days)
request_url += '&aqi=' + 'no'
request_url += '&alerts=' + 'no'

r = requests.get(request_url)

if r.status_code == 200:

    weather_data = json.loads(r.text)

    for day in weather_data['forecast']['forecastday']:
        for hour in day['hour']:

            if hour['time'] >= weatherapi_now_time:
                rainlist[hour['time']] = hour['precip_mm']


for entry in rainlist:
    print(entry + ': ' + str(rainlist[entry]))