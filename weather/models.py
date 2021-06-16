import random
import datetime
import requests
import csv
import json
from django.db import models
from django.utils import timezone
from bs4 import BeautifulSoup
from django.conf import settings


def get_data_from_drops(latitude, longtitude):

    url = 'https://www.drops.live/' + latitude + "," + longtitude
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'lxml')
    temperature_raw_value = soup.find('span', class_="temp temp left")
    if not temperature_raw_value:
        return None
    temperature = int(temperature_raw_value.text[:-1])
    if temperature <= 10:
        color = "blue"
    elif temperature >= 11 and temperature <= 24:
        color = "green"
    else:
        color = "orange"
    icon = soup.find('img', class_='icon left')
    icon_src = 'https://www.drops.live' + icon['src']
    city = soup.find('span', class_='city').text
    display_that = {'temperature': str(temperature),
                    'city': city, 'icon': icon_src, 'color': color}

    return display_that


class WeatherLocationManager(models.Manager):

    def change_temperature(self, dt):
        for weather_location in self.all():
            weather_location.change_temperature(dt)

    def recent_results(self):
        return self.all().order_by('access_datetime')[:5]

    def create_random_locations(self, count):
        i = 0
        while i < count:
            latitude = str(round(random.uniform(-90, 90), 6))
            longtitude = str(round(random.uniform(-180, 180), 6))
            context = get_data_from_drops(latitude, longtitude)
            if not context:
                continue
            print(context)
            self.create(
                icon=context['icon'],
                location=latitude+","+longtitude,
                temperature=context['temperature'],
                city=context['city'])
            i += 1


class WeatherLocation(models.Model):
    access_datetime = models.DateTimeField(auto_now_add=True)
    icon = models.CharField(max_length=50)
    location = models.CharField(max_length=50)
    temperature = models.CharField(max_length=10)
    city = models.CharField(max_length=20)

    objects = WeatherLocationManager()

    def change_temperature(self, dt):
        int_temperature = int(self.temperature[:-1])
        self.temperature = str(int_temperature + dt) + self.temperature[-1]
        self.save()

# POLAND MODEL MANAGERS


class VoivodeshipManager(models.Manager):
    def get_voivodeships(self):
        with open('weather/wojewodztwa.csv', 'r', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';')
            next(csvreader)
            for row in csvreader:
                voivo = Voivodeship(name=row[1])
                voivo.save()


class DistrictManager(models.Manager):
    def get_districts(self):
        with open('weather/powiaty.csv', 'r', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';')
            next(csvreader)
            for row in csvreader:
                voivo_id = int(int(row[1])/2)
                district = District(
                    name=row[2], voivodeship=Voivodeship(id=voivo_id))
                district.save()


class LocationManager(models.Manager):
    def get_weather_data_for_town(self, town_n, district_n):
        url = f'http://api.openweathermap.org/data/2.5/weather?q={town_n}&appid={settings.OPENWEATHER_KEY}'
        response = requests.get(url).json()
        if response['cod'] == '404':
            return 0
        temperature_kelvin = response['main']['temp']
        temperature_celsius = int(float(temperature_kelvin) - 273.15)
        if District.objects.filter(name=district_n).count() > 1:
            for dup in District.objects.filter(name=district_n):
                dup_id = dup.id
            District.objects.filter(id=dup_id).delete()
        if Town.objects.filter(name=town_n).count() > 1:
            for dup in Town.objects.filter(name=town_n):
                dup_id = dup.id
            TemperatureData.objects.filter(id=dup_id).delete()
            Town.objects.filter(id=dup_id).delete()

        location = Town(district=District.objects.get(
            name=district_n), name=town_n)
        location.save()
        temperature = TemperatureData(town=Town.objects.get(
            name=town_n), value=temperature_celsius,
            timestamp=datetime.datetime.now(datetime.timezone.utc))
        temperature.save()

# FOR POLAND


class Voivodeship(models.Model):
    name = models.CharField(unique=True, max_length=50)

    objects = VoivodeshipManager()


class District(models.Model):
    voivodeship = models.ForeignKey(
        'weather.Voivodeship', on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=50)

    objects = DistrictManager()


class Town(models.Model):
    district = models.ForeignKey(
        'weather.District', on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=50)

    objects = LocationManager()


class TemperatureData(models.Model):
    town = models.ForeignKey('weather.Town', on_delete=models.DO_NOTHING)
    value = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)

    objects = LocationManager()
