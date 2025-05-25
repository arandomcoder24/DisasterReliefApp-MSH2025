from flask import Flask, render_template, request
import requests
import math

app = Flask(__name__)

TOMORROW_API_KEY = 'mI80Id6dmOJZMAIrUrAe4w3oDVuRRb7k'

@app.route("/")
def home():
    # Try to get lat/lon from query parameters (sent from frontend geolocation)
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)

    city = "Unknown Location"

    if lat is None or lon is None:
        # Fallback: get user IP-based location
        user_ip = request.remote_addr
        loc_url = f"http://ip-api.com/json/{user_ip}"
        loc_response = requests.get(loc_url)
        loc_data = loc_response.json()
        lat = loc_data.get("lat", 45.4353)
        lon = loc_data.get("lon", 28.0080)
        city = loc_data.get("city", "Unknown City")
    else:
        # Optional: reverse geocode lat/lon to get city name
        # For example, you could use a free reverse geocoding API here
        city = "Your Location"

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
    severe_codes = [4201, 5101, 6000, 6001, 6201, 7000, 7101, 7102, 8000]

    # Get current weather data
    realtime_url = "https://api.tomorrow.io/v4/weather/realtime"
    realtime_params = {
        "location": f"{lat},{lon}",
        "fields": "temperature,weatherCode,stormSeverity",
        "apikey": TOMORROW_API_KEY
    }
    realtime_response = requests.get(realtime_url, params=realtime_params)
    realtime_data = realtime_response.json()

    values = realtime_data.get("data", {}).get("values", {})
    temperature = values.get("temperature", None)
    if temperature is not None:
        temperature = round(temperature * 1.8 + 32, 2)  # Convert to °F
    else:
        temperature = "N/A"

    weather_code = values.get("weatherCode", 0)
    storm_severity = values.get("stormSeverity", "None")
    condition = code_descriptions.get(weather_code, "Unknown")

    dx = dy = direction = speed = None

    if weather_code in severe_codes:
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

        timelines = forecast_data.get("data", {}).get("timelines", [])
        if timelines:
            intervals = timelines[0].get("intervals", [])
            if intervals:
                first_interval = intervals[0]
                direction = first_interval["values"].get("windDirection", 0)
                speed = first_interval["values"].get("windSpeed", 0)

                angle_rad = math.radians(direction)
                dx = math.sin(angle_rad)
                dy = math.cos(angle_rad)
            else:
                direction = speed = dx = dy = None
        else:
            direction = speed = dx = dy = None

    elif 3000 < weather_code < 4000:
        alert = "Moderate weather nearby"
    elif 4000 < weather_code < 4201:
        alert = "Moderate weather nearby, take precaution"
    else:
        alert = "No severe weather nearby"

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
