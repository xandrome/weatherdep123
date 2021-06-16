import datetime
import requests
import random
import csv
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from bs4 import BeautifulSoup
from weather.models import WeatherLocation, Voivodeship, District, Town, TemperatureData

degree_sign = u'\N{DEGREE SIGN}'


def get_data_from_drops(latitude, longtitude):

    url = 'https://www.drops.live/' + latitude + "," + longtitude
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'lxml')
    temperature_raw_value = soup.find('span', class_="temp temp left").text
    temperature = int(temperature_raw_value[:-1])
    if temperature <= 10:
        color = "blue"
    elif temperature >= 11 and temperature <= 24:
        color = "green"
    else:
        color = "orange"
    icon = soup.find('img', class_='icon left')
    icon_src = 'https://www.drops.live' + icon['src']
    city = soup.find('span', class_='city').text
    display_that = {'temperature': temperature_raw_value,
                    'city': city, 'icon': icon_src, 'color': color}

    return display_that


def index(request, latitude, longtitude):

    current_date = datetime.datetime.now(datetime.timezone.utc)
    template = loader.get_template('weather/index.html')
    last_access = WeatherLocation.objects.filter(
        location=latitude+","+longtitude).order_by('-access_datetime')
    is_in_db = last_access.exists() and (
        current_date - last_access[0].access_datetime).seconds <= 300
    if is_in_db:
        context = {'temperature': last_access[0].temperature, 'city': last_access[0].city, 'icon': last_access[0].icon,
                   'color': last_access[0].color}
    else:
        context = get_data_from_drops(latitude, longtitude)
        db = WeatherLocation(access_datetime=datetime.datetime.now(), icon=context['icon'], location=latitude+","+longtitude,
                             temperature=context['temperature'], city=context['city'])
        db.save()
    return HttpResponse(template.render(context, request))


def display_log_table(request):
    # random_logs()
    query_list = WeatherLocation.objects.all().order_by('-access_datetime')
    context = {'query_list': query_list}
    return render(request, 'weather/logs.html', context)


def random_logs():
    for query in range(10):
        latitude = str(round(random.uniform(-90, 90), 6))
        longtitude = str(round(random.uniform(-180, 180), 6))
        context = get_data_from_drops(latitude, longtitude)
        db = WeatherLocation(access_datetime=datetime.datetime.now(), icon=context['icon'],
                             location=latitude+","+longtitude,
                             temperature=context['temperature'], city=context['city'])
        db.save()


def get_weather_data_to_every_location():
    with open('weather/miasta.csv', 'r', encoding='utf-8') as csvfile:
        for line in csv.reader(csvfile, delimiter=';'):
            Town.objects.get_weather_data_for_town(line[0], line[1])


def average_temperature_voivo(request, voivo):
    while True:
        voivo = voivo.upper()
        current_datetime = datetime.datetime.now()
        voivo_name = TemperatureData.objects.filter(
            town__district__voivodeship__name__startswith=voivo)[0].town.district.voivodeship.name
        last_access = TemperatureData.objects.filter(
            town__district__voivodeship__name__startswith=voivo).order_by('-timestamp')
        is_in_db = last_access.exists() and (
            current_datetime - last_access[0].timestamp).seconds <= 900
        fifteen_minutes = datetime.timedelta(minutes=15)
        name_list = []
        if is_in_db:

            location_voivo_name = TemperatureData.objects.filter(town__district__voivodeship__name__startswith=voivo).filter(
                timestamp__date__gte=current_datetime - fifteen_minutes)
            count = 0
            sum_temp = 0
            for temp in location_voivo_name:
                if temp.town.name not in name_list:
                    sum_temp += temp.value
                    count += 1
                    name_list.append(temp.town.name)
            average_temp = round(sum_temp/count, 2)
            context = {'average': str(
                average_temp) + degree_sign, 'voi': location_voivo_name, 'voivo_name': voivo_name}
            break
        else:
            voivodship = TemperatureData.objects.filter(
                town__district__voivodeship__name__startswith=voivo)
            for data in voivodship:
                if data.town.name not in name_list:
                    TemperatureData.objects.get_weather_data_for_town(
                        data.town.name, data.town.district.name)
                    name_list.append(data.town.name)
            name_list.clear()
    return HttpResponse(loader.get_template('weather/average.html').render(context, request))
