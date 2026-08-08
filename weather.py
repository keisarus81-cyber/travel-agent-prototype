import requests


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather_description(code):
    descriptions = {
        0: "שמיים בהירים",
        1: "בעיקר בהיר",
        2: "מעונן חלקית",
        3: "מעונן",
        45: "ערפל",
        48: "ערפל",
        51: "טפטוף קל",
        53: "טפטוף",
        55: "טפטוף חזק",
        61: "גשם קל",
        63: "גשם",
        65: "גשם חזק",
        71: "שלג קל",
        73: "שלג",
        75: "שלג כבד",
        80: "ממטרים קלים",
        81: "ממטרים",
        82: "ממטרים חזקים",
        95: "סופת רעמים",
        96: "סופת רעמים",
        99: "סופת רעמים חזקה",
    }

    return descriptions.get(code, "מזג אוויר לא ידוע")


def get_weather_forecast(latitude, longitude, days=7):

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "precipitation_sum"
        ]),

        "timezone": "auto",
        "forecast_days": days
    }

    try:
        response = requests.get(
            WEATHER_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        daily = data.get("daily")

        if not daily:
            return []

        forecast = []

        for i in range(len(daily["time"])):

            weather_code = daily["weather_code"][i]

            forecast.append({
                "date": daily["time"][i],

                "weather_code": weather_code,

                "description":
                    get_weather_description(weather_code),

                "max_temp":
                    daily["temperature_2m_max"][i],

                "min_temp":
                    daily["temperature_2m_min"][i],

                "rain_probability":
                    daily["precipitation_probability_max"][i],

                "precipitation":
                    daily["precipitation_sum"][i]
            })

        return forecast

    except requests.RequestException as error:
        print(f"Weather API error: {error}")
        return []