import requests
import os
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

load_dotenv()

WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")


def get_weather_info(city_name):
    try:
        url = f"http://api.weatherstack.com/current?access_key={WEATHERSTACK_API_KEY}&query={city_name}"
        response = requests.get(url)
        data = response.json()

        if "error" in data:
            return None, "Weather data not available"

        temp = data["current"]["temperature"]
        weather_desc = data["current"]["weather_descriptions"][0]
        icon_url = data["current"]["weather_icons"][0]
        feelslike = data["current"]["feelslike"]
        humidity = data["current"]["humidity"]
        wind_speed = data["current"]["wind_speed"]

        weather_info = {
            "description": weather_desc,
            "temperature": temp,
            "feelslike": feelslike,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "icon": icon_url
        }

        return weather_info, None

    except Exception as e:
        return None, f"Something went wrong: {e}"

        
def get_coordinates(city_name):
    try:
        geolocator = Nominatim(user_agent="travel_planner")
        location = geolocator.geocode(city_name)
        if location:
            return [location.latitude, location.longitude]
    except:
        pass
    return None







