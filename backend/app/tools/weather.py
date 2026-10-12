from datetime import datetime, timezone
from typing import Any
import httpx
from app.config import get_settings


async def get_weather(location: str, units: str = "metric") -> dict[str, Any]:
    settings = get_settings()
    api_key = settings.weather_api_key.strip()

    if not api_key:
        return {
            "success": False,
            "location": location,
            "error": "Weather provider API key is not configured. Please set WEATHER_API_KEY in the environment.",
            "data": None,
        }

    clean_location = location.strip()
    if not clean_location:
        return {
            "success": False,
            "location": location,
            "error": "Location parameter cannot be empty.",
            "data": None,
        }

    valid_units = "imperial" if units.lower() in ("imperial", "fahrenheit", "f") else "metric"
    unit_symbol = "°F" if valid_units == "imperial" else "°C"
    speed_unit = "mph" if valid_units == "imperial" else "m/s"

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": clean_location,
        "appid": api_key,
        "units": valid_units,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

        if response.status_code == 404:
            return {
                "success": False,
                "location": clean_location,
                "error": f"Location '{clean_location}' was not found. Please verify the city name.",
                "data": None,
            }

        if response.status_code == 401:
            return {
                "success": False,
                "location": clean_location,
                "error": "Weather provider authentication failed. Invalid API key.",
                "data": None,
            }

        response.raise_for_status()
        raw = response.json()

        weather_desc = ""
        weather_main = ""
        if raw.get("weather") and len(raw["weather"]) > 0:
            weather_main = raw["weather"][0].get("main", "")
            weather_desc = raw["weather"][0].get("description", "")

        main_info = raw.get("main", {})
        wind_info = raw.get("wind", {})
        dt_val = raw.get("dt")
        obs_time = (
            datetime.fromtimestamp(dt_val, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            if dt_val
            else None
        )

        weather_data = {
            "city": raw.get("name", clean_location),
            "country": raw.get("sys", {}).get("country", ""),
            "condition": weather_main,
            "description": weather_desc.capitalize(),
            "temperature": f"{main_info.get('temp', 0)}{unit_symbol}",
            "feels_like": f"{main_info.get('feels_like', 0)}{unit_symbol}",
            "humidity": f"{main_info.get('humidity', 0)}%",
            "pressure": f"{main_info.get('pressure', 0)} hPa",
            "wind": f"{wind_info.get('speed', 0)} {speed_unit}",
            "units": valid_units,
            "observation_time": obs_time,
        }

        return {
            "success": True,
            "location": weather_data["city"],
            "data": weather_data,
            "error": None,
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "location": clean_location,
            "error": "Weather service request timed out.",
            "data": None,
        }
    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "location": clean_location,
            "error": f"Weather service HTTP error: {exc.response.status_code}",
            "data": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "location": clean_location,
            "error": f"Failed to fetch weather: {str(exc)}",
            "data": None,
        }
