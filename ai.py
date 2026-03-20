import requests
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import pyttsx3
import speech_recognition as sr
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# -------------------------------
# Weather Class
# -------------------------------
class WeatherForecaster:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")

        if not self.api_key:
            raise ValueError("API_KEY not found. Please set it in environment variables or .env file.")

        self.base_url = "http://api.openweathermap.org/data/2.5/"
    
    def get_current_weather(self, city_name, units="metric"):
        url = f"{self.base_url}weather?q={city_name}&appid={self.api_key}&units={units}"
        response = requests.get(url)
        data = response.json()

        if data["cod"] != 200:
            print(f"Error: {data['message']}")
            return None

        return self._process_current_weather(data)
    
    def get_forecast(self, city_name, units="metric"):
        url = f"{self.base_url}forecast?q={city_name}&appid={self.api_key}&units={units}"
        response = requests.get(url)
        data = response.json()

        if data["cod"] != "200":
            print(f"Error: {data['message']}")
            return None

        return self._process_forecast(data)
    
    def _process_current_weather(self, data):
        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "wind_direction": data["wind"].get("deg", "N/A"),
            "weather": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime('%H:%M'),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime('%H:%M'),
            "time": datetime.fromtimestamp(data["dt"]).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _process_forecast(self, data):
        forecast_list = []
        city = data["city"]["name"]
        country = data["city"]["country"]

        for item in data["list"]:
            forecast = {
                "datetime": datetime.fromtimestamp(item["dt"]).strftime('%Y-%m-%d %H:%M:%S'),
                "date": datetime.fromtimestamp(item["dt"]).strftime('%Y-%m-%d'),
                "time": datetime.fromtimestamp(item["dt"]).strftime('%H:%M'),
                "temperature": item["main"]["temp"],
                "feels_like": item["main"]["feels_like"],
                "humidity": item["main"]["humidity"],
                "pressure": item["main"]["pressure"],
                "wind_speed": item["wind"]["speed"],
                "wind_direction": item["wind"].get("deg", "N/A"),
                "weather": item["weather"][0]["main"],
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"],
                "pop": item.get("pop", 0) * 100
            }
            forecast_list.append(forecast)

        return {
            "city": city,
            "country": country,
            "forecasts": forecast_list
        }
    
    def display_current_weather(self, weather_data):
        if not weather_data:
            return

        print("\n" + "="*50)
        print(f"Current Weather in {weather_data['city']}, {weather_data['country']}")
        print("="*50)
        print(f"Temperature: {weather_data['temperature']}°C (Feels like {weather_data['feels_like']}°C)")
        print(f"Weather: {weather_data['weather']} - {weather_data['description']}")
        print(f"Humidity: {weather_data['humidity']}%")
        print(f"Pressure: {weather_data['pressure']} hPa")
        print(f"Wind: {weather_data['wind_speed']} m/s at {weather_data['wind_direction']}°")
        print(f"Sunrise: {weather_data['sunrise']}, Sunset: {weather_data['sunset']}")
        print(f"Last updated: {weather_data['time']}")
        print("="*50 + "\n")

    def get_weather_speech(self, weather_data):
        if not weather_data:
            return "Sorry, I could not fetch the weather data."

        return (
            f"The current weather in {weather_data['city']}, {weather_data['country']} is {weather_data['weather']} "
            f"with {weather_data['description']}. The temperature is {weather_data['temperature']} degrees Celsius, "
            f"but feels like {weather_data['feels_like']} degrees. Humidity is at {weather_data['humidity']} percent, "
            f"wind speed is {weather_data['wind_speed']} meters per second. Sunrise is at {weather_data['sunrise']} "
            f"and sunset is at {weather_data['sunset']}."
        )

    def plot_forecast(self, forecast_data):
        if not forecast_data:
            return

        df = pd.DataFrame(forecast_data["forecasts"])
        df['datetime'] = pd.to_datetime(df['datetime'])

        daily = df.groupby('date').agg({
            'temperature': ['mean', 'min', 'max'],
            'humidity': 'mean',
            'pop': 'max'
        })

        plt.figure(figsize=(12, 6))

        plt.subplot(2, 1, 1)
        plt.plot(daily.index, daily['temperature']['mean'], marker='o')
        plt.fill_between(daily.index, daily['temperature']['min'], daily['temperature']['max'], alpha=0.2)
        plt.title(f"5-Day Weather Forecast for {forecast_data['city']}, {forecast_data['country']}")
        plt.ylabel("Temperature (°C)")
        plt.grid(True)

        plt.subplot(2, 1, 2)
        plt.bar(daily.index, daily['humidity']['mean'], alpha=0.6)
        plt.plot(daily.index, daily['pop']['max'], marker='o')
        plt.ylabel("Humidity (%) / Rain Chance (%)")
        plt.xlabel("Date")
        plt.grid(True)

        plt.tight_layout()
        plt.show()

# -------------------------------
# Voice Setup
# -------------------------------
engine = pyttsx3.init()

def speak(text):
    print("🔈 AI:", text)
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = r.listen(source)

    try:
        command = r.recognize_google(audio)
        print("🗨️ You said:", command)
        return command.lower()

    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return ""

    except sr.RequestError:
        speak("Sorry, I couldn't reach the voice recognition service.")
        return ""

# -------------------------------
# Chatbot Logic
# -------------------------------
def chatbot():
    forecaster = WeatherForecaster()

    speak("Hello! I’m your AI Weather Assistant.")
    speak("Say 'current' to get the current weather.")
    speak("Say 'forecast' to see a 5-day weather forecast.")
    speak("Say 'exit' to leave.")

    while True:
        user_input = listen()

        if 'exit' in user_input or 'quit' in user_input or 'bye' in user_input:
            speak("Goodbye! Stay safe and have a great day!")
            break

        elif 'current' in user_input:
            speak("Which city's current weather would you like to know?")
            city = listen()

            if not city.strip():
                speak("Sorry, I didn’t catch the city name.")
                continue

            weather = forecaster.get_current_weather(city)

            if weather:
                forecaster.display_current_weather(weather)
                speak(forecaster.get_weather_speech(weather))
            else:
                speak("Sorry, I couldn’t retrieve weather information.")

        elif 'forecast' in user_input:
            speak("Which city's forecast would you like to see?")
            city = listen()

            if not city.strip():
                speak("Sorry, I didn’t catch the city name.")
                continue

            forecast = forecaster.get_forecast(city)

            if forecast:
                speak(f"Here is the 5-day forecast for {city}.")
                forecaster.plot_forecast(forecast)
            else:
                speak("Sorry, I couldn’t retrieve the forecast.")

        else:
            speak("Please say 'current', 'forecast', or 'exit'.")

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    chatbot()
