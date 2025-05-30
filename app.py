from flask import Flask, render_template, request, jsonify
import requests
import math
import openai

app = Flask(__name__)

TOMORROW_API_KEY = 'mI80Id6dmOJZMAIrUrAe4w3oDVuRRb7k'

code_descriptions = {
    0: "Unknown", 1000: "Clear", 1001: "Cloudy", 1100: "Mostly Clear", 1101: "Partly Cloudy",
    1102: "Mostly Cloudy",
    2000: "Fog", 2100: "Light Fog", 3000: "Light Wind", 3001: "Wind", 3002: "Strong Wind",
    4000: "Drizzle", 4001: "Rain", 4200: "Light Rain", 4201: "Heavy Rain",
    5000: "Snow", 5001: "Flurries", 5100: "Light Snow", 5101: "Heavy Snow",
    6000: "Freezing Drizzle", 6001: "Freezing Rain", 6200: "Light Freezing Rain", 6201: "Heavy Freezing Rain",
    7000: "Ice Pellets", 7101: "Heavy Ice Pellets", 7102: "Light Ice Pellets", 8000: "Thunderstorm"
}

severe_codes = [4201, 5101, 6000, 6001, 6201, 7000, 7101, 7102, 8000]

forecast_url = "https://api.tomorrow.io/v4/weather/forecast"

realtime_url = "https://api.tomorrow.io/v4/weather/realtime"

url = "https://nominatim.openstreetmap.org/reverse"


@app.route("/", methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return "Missing JSON data", 400

        lat = data.get("lat")
        lon = data.get("lon")

        parameters = {"lat": lat, "lon": lon, "format": "json"}
        headers = {"User-Agent": "WeatherMapApp/1.0"}
        response = requests.get(url, params=parameters, headers=headers)
        location_data = response.json()
        address = location_data.get("address", {})
        city = address.get("city") or address.get("town") or address.get("village") or "Your Location"

        realtime_params = {
            "location": f"{lat},{lon}",
            "fields": "temperature,weatherCode,stormSeverity",
            "apikey": TOMORROW_API_KEY
        }
        realtime_response = requests.get(realtime_url, params=realtime_params)
        realtime_data = realtime_response.json()

        values = realtime_data.get("data", {}).get("values", {})
        temperature = values.get("temperature")
        if temperature is not None:
            temperature = round(temperature * 1.8 + 32, 2)
        else:
            temperature = "N/A"

        weather_code = values.get("weatherCode", 0)
        storm_severity = values.get("stormSeverity", "None")
        condition = code_descriptions.get(weather_code, "Unknown")

        dx = dy = direction = speed = None

        if weather_code in severe_codes:
            alert = f"Severe weather detected: {storm_severity}"

            forecast_params = {
                "location": f"{lat},{lon}",
                "fields": "windDirection,windSpeed",
                "apikey": TOMORROW_API_KEY,
                "timestamps": "1h"
            }
            forecast_response = requests.get(forecast_url, params=forecast_params)
            forecast_data = forecast_response.json()

            intervals = forecast_data.get("data", {}).get("timelines", [{}])[0].get("intervals", [])
            if intervals:
                first_interval = intervals[0]
                direction = first_interval["values"].get("windDirection", 0)
                speed = first_interval["values"].get("windSpeed", 0)

                angle_rad = math.radians(direction)
                dx = math.sin(angle_rad)
                dy = math.cos(angle_rad)
        elif 3000 < weather_code < 4000:
            alert = "Moderate weather nearby"
        elif 4000 < weather_code < 4201:
            alert = "Moderate rain or drizzle nearby"
        else:
            alert = "No severe weather nearby"

        if lat is None or lon is None:
            return "Missing lat/lon", 400
        return jsonify({"city": city,
                        "speed": speed,
                        "dx": dx,
                        "dy": dy,
                        "alert": alert,
                        "temperature": temperature,
                        "condition": condition,
                        "lat": lat,
                        "lon": lon
                        })
    else:
        # Default location (e.g., NYC)
        lat, lon = 40.7128, -74.0060

        city = "New York"
        realtime_params = {
            "location": f"{lat},{lon}",
            "fields": "temperature,weatherCode,stormSeverity",
            "apikey": TOMORROW_API_KEY
        }
        realtime_response = requests.get(realtime_url, params=realtime_params)
        realtime_data = realtime_response.json()

        values = realtime_data.get("data", {}).get("values", {})
        temperature = values.get("temperature")
        if temperature is not None:
            temperature = round(temperature * 1.8 + 32, 2)
        else:
            temperature = "N/A"

        weather_code = values.get("weatherCode", 0)
        storm_severity = values.get("stormSeverity", "None")
        condition = code_descriptions.get(weather_code, "Unknown")

        dx = dy = direction = speed = None

        if weather_code in severe_codes:
            alert = f"Severe weather detected: {storm_severity}"

            forecast_params = {
                "location": f"{lat},{lon}",
                "fields": "windDirection,windSpeed",
                "apikey": TOMORROW_API_KEY,
                "timestamps": "1h"
            }
            forecast_response = requests.get(forecast_url, params=forecast_params)
            forecast_data = forecast_response.json()

            intervals = forecast_data.get("data", {}).get("timelines", [{}])[0].get("intervals", [])
            if intervals:
                first_interval = intervals[0]
                direction = first_interval["values"].get("windDirection", 0)
                speed = first_interval["values"].get("windSpeed", 0)

                angle_rad = math.radians(direction)
                dx = math.sin(angle_rad)
                dy = math.cos(angle_rad)
        elif 3000 < weather_code < 4000:
            alert = "Moderate weather nearby"
        elif 4000 < weather_code < 4201:
            alert = "Moderate rain or drizzle nearby"
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
