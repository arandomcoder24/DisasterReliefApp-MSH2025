from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests
import math

app = Flask(__name__)

TOMORROW_API_KEY = 'mI80Id6dmOJZMAIrUrAe4w3oDVuRRb7k'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///system.db'
db = SQLAlchemy(app)



@app.route("/")
def home():
    user_ip = request.remote_addr

    # Get user location
    loc_url = f"http://ip-api.com/json/{user_ip}"
    loc_response = requests.get(loc_url)
    loc_data = loc_response.json()

    lat = loc_data.get("lat", 37.5485)  # Fremont default
    lon = loc_data.get("lon", -121.9886)
    city = loc_data.get("city", "Unknown")

    # Weather code meanings
    code_descriptions = {
        0: "Unknown",
        1000: "Clear",
        1001: "Cloudy",
        1100: "Mostly Clear",
        1101: "Partly Cloudy",
        1102: "Mostly Cloudy",
        2000: "Fog",
        2100: "Light Fog",
        3000: "Light Wind",
        3001: "Wind",
        3002: "Strong Wind",
        4000: "Drizzle",
        4001: "Rain",
        4200: "Light Rain",
        4201: "Heavy Rain",
        5000: "Snow",
        5001: "Flurries",
        5100: "Light Snow",
        5101: "Heavy Snow",
        6000: "Freezing Drizzle",
        6001: "Freezing Rain",
        6200: "Light Freezing Rain",
        6201: "Heavy Freezing Rain",
        7000: "Ice Pellets",
        7101: "Heavy Ice Pellets",
        7102: "Light Ice Pellets",
        8000: "Thunderstorm"
    }

    # Get current weather data
    realtime_url = "https://api.tomorrow.io/v4/weather/realtime"
    realtime_params = {
        "location": f"{lat},{lon}",
        "fields": "temperature,weatherCode,stormSeverity",
        "apikey": TOMORROW_API_KEY
    }
    realtime_response = requests.get(realtime_url, params=realtime_params)
    realtime_data = realtime_response.json()

    # Extract realtime values
    values = realtime_data.get("data", {}).get("values", {})
    temperature = values.get("temperature", "N/A")
    weather_code = values.get("weatherCode", 0)
    storm_severity = values.get("stormSeverity", "None")
    condition = code_descriptions.get(weather_code, "Unknown")

    dx = dy = direction = speed = None
    if storm_severity != "None":
        alert = f"Severe weather detected: {storm_severity}"

        # Forecast for wind direction/speed
        forecast_url = "https://api.tomorrow.io/v4/weather/forecast"
        forecast_params = {
            "location": f"{lat},{lon}",
            "fields": "windDirection,windSpeed",
            "apikey": TOMORROW_API_KEY,
            "timestamps": "1h"
        }
        forecast_response = requests.get(forecast_url, params=forecast_params)
        forecast_data = forecast_response.json()

        intervals = forecast_data.get("data", {}).get("timelines", [])[0].get("intervals", [])
        if intervals:
            first_interval = intervals[0]
            direction = first_interval["values"].get("windDirection", 0)
            speed = first_interval["values"].get("windSpeed", 0)

            angle_rad = math.radians(direction)
            dx = math.sin(angle_rad)
            dy = math.cos(angle_rad)
    else:
        alert = "No severe weather nearby"

    # Render template
    return render_template("front-end.html",
                           city=city,
                           temperature=temperature,
                           condition=condition,
                           alert=alert,
                           dx=dx,
                           dy=dy,
                           lat=lat,
                           lon=lon,
                           wind_dir=direction,
                           wind_speed=speed)

if __name__ == "__main__":
    app.run(debug=True)
