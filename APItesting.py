import pprint as p
import datetime

from jinja2 import Environment, FileSystemLoader

import openmeteo_requests
import os
import webbrowser
import pandas as pd
import requests_cache
from retry_requests import retry
from pprint import pprint as pp

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

cities = {
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
    "Chicago": {"lat": 41.8781, "lon": -87.6298},
    "Houston": {"lat": 29.7604, "lon": -95.3698},
    "Miami": {"lat": 25.7617, "lon": -80.1918},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Berlin": {"lat": 52.5200, "lon": 13.4050},
    "Madrid": {"lat": 40.4168, "lon": -3.7038},
    "Rome": {"lat": 41.9028, "lon": 12.4964},
    "Tokyo": {"lat": 35.6895, "lon": 139.6917},
    "Beijing": {"lat": 39.9042, "lon": 116.4074},
    "Seoul": {"lat": 37.5665, "lon": 126.9780},
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Toronto": {"lat": 43.6532, "lon": -79.3832},
    "Mexico City": {"lat": 19.4326, "lon": -99.1332},
    "São Paulo": {"lat": -23.5505, "lon": -46.6333},
    "Johannesburg": {"lat": -26.2041, "lon": 28.0473},
    "Dubai": {"lat": 25.276987, "lon": 55.296249},
    "Moscow": {"lat": 55.7558, "lon": 37.6173}
}

weather_codes = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Drizzle: Light intensity",
    53: "Drizzle: Moderate intensity",
    55: "Drizzle: Dense intensity",
    56: "Freezing Drizzle: Light intensity",
    57: "Freezing Drizzle: Dense intensity",
    61: "Rain: Slight intensity",
    63: "Rain: Moderate intensity",
    65: "Rain: Heavy intensity",
    66: "Freezing Rain: Light intensity",
    67: "Freezing Rain: Heavy intensity",
    71: "Snow fall: Slight intensity",
    73: "Snow fall: Moderate intensity",
    75: "Snow fall: Heavy intensity",
    77: "Snow grains",
    80: "Rain showers: Slight",
    81: "Rain showers: Moderate",
    82: "Rain showers: Violent",
    85: "Snow showers: Slight",
    86: "Snow showers: Heavy",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"

input_city = input("Enter the name of the city: ").title()
if not input_city in cities:
    print("City not found. Don't joke with us!")
    exit()

url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": cities[input_city]["lat"],
	"longitude": cities[input_city]["lon"],
	"daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "wind_speed_10m_max", "wind_direction_10m_dominant"],
	"forecast_days": 1,
}

responses = openmeteo.weather_api(url, params=params)

response = responses[0]

# Process first location. Add a for-loop for multiple locations or weather models
print(response)

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_weather_code = daily.Variables(0).ValuesAsNumpy()
daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
daily_wind_speed_10m_max = daily.Variables(3).ValuesAsNumpy()
daily_wind_direction_10m_dominant = daily.Variables(4).ValuesAsNumpy()

daily_data = {"date": pd.date_range(
	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily.Interval()),
	inclusive = "left"
)}

daily_data["weather_code"] = weather_codes[int(daily_weather_code[0])]
daily_data["temperature_2m_max"] = daily_temperature_2m_max
daily_data["temperature_2m_min"] = daily_temperature_2m_min
daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
daily_data["wind_direction_10m_dominant"] = daily_wind_direction_10m_dominant

daily_dataframe = pd.DataFrame(data = daily_data)
# print("\nDaily data\n", daily_dataframe)
# pp(daily_dataframe.to_dict(orient="records"))

env = Environment(loader=FileSystemLoader("."))

template = env.get_template("template.html.j2")

weather_values = dict(daily_dataframe.to_dict(orient="records")[0])

weather_values["Date"] = weather_values.pop("date")
weather_values["Weather_Status"] = weather_values.pop("weather_code")
weather_values["Temerature(2m_max)"] = round(weather_values.pop("temperature_2m_max"),2)
weather_values["Temerature(2m_min)"] = round(weather_values.pop("temperature_2m_min"),2)
weather_values["Wind_speed(10m_max)"] = round(weather_values.pop("wind_speed_10m_max"),2)
weather_values["Wind_direction(10m_dominant)"] = round(weather_values.pop("wind_direction_10m_dominant"),2)


context = {
    "title": "Weather Report",
    "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "city": input_city,
    "weather": weather_values
}

# print(weather_values)

html = template.render(context)

with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Wrote report.html")

webbrowser.open(f"file://{os.path.realpath('report.html')}")