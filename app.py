from flask import Flask, render_template, request
import requests, math

app = Flask(__name__)

@app.route("/")
def home():
    # Get user IP and location
    user_ip = request.remote_addr
    loc_url = f"http://ip-api.com/json/{user_ip}"
    loc_data = requests.get(loc_url).json()
    lat = loc_data.get("lat", 37.5485)
    lon = loc_data.get("lon", -121.9886)
    city = loc_data.get("city", "Unknown")

    # Weather data
    TOMORROW_API_KEY = 'mI80Id6dmOJZMAIrUrAe4w3oDVuRRb7k'
    code_descriptions = {
        1000: "Clear", 1001: "Cloudy", 1100: "Mostly Clear",
        1101: "Partly Cloudy", 1102: "Mostly Cloudy", 8000: "Thunderstorm",
        4000: "Drizzle", 4001: "Rain", 4200: "Light Rain", 4201: "Heavy Rain"
        # (Add more as needed)
    }

    weather_url = "https://api.tomorrow.io/v4/weather/realtime"
    weather = requests.get(weather_url, params={
        "location": f"{lat},{lon}",
        "fields": "temperature,weatherCode,stormSeverity",
        "apikey": TOMORROW_API_KEY
    }).json()

    values = weather.get("data", {}).get("values", {})
    temperature = values.get("temperature", "N/A")
    code = values.get("weatherCode", 0)
    condition = code_descriptions.get(code, "Unknown")
    storm = values.get("stormSeverity", "None")

    alert = f"Storm: {storm}" if storm != "None" else "No severe weather"

    return render_template("front-end.html",
                           city=city, temperature=temperature,
                           condition=condition, alert=alert,
                           lat=lat, lon=lon)
