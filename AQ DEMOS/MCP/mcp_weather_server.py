import os
from typing import Any, Literal, cast

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP  # Reverted to original import

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
OPENWEATHER_API_BASE = "https://api.openweathermap.org/data/3.0/onecall"
USER_AGENT = "weather-app/1.0"
# Get API key from environment variable
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Validate API key
if not OPENWEATHER_API_KEY:
    print("WARNING: OpenWeatherMap API key not found in environment variables.")
    print("Please set the OPENWEATHER_API_KEY environment variable or create a .env file.")
    print("You can get an API key from https://openweathermap.org/api")


async def make_weather_request(url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Make a request to the OpenWeatherMap API with proper error handling."""
    if params is None:
        params = {}

    # Always include the API key
    params["appid"] = OPENWEATHER_API_KEY

    # Set up headers
    headers = {"User-Agent": USER_AGENT}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)

            # Check if the request was successful
            if response.status_code == 200:
                return response.json()
            else:
                # For debugging purposes, print the error
                print(f"API request failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return response.json()  # Return the error response for handling
    except Exception as e:
        print(f"Error making API request: {str(e)}")
        return None


async def get_coordinates(city: str, country_code: str = "", state_code: str = "") -> tuple[float, float] | None:
    """Get coordinates for a location using OpenWeatherMap Geocoding API."""
    # First try the direct geocoding API
    url = "https://api.openweathermap.org/geo/1.0/direct"

    # Build the query string
    q = city
    if state_code and country_code:
        q = f"{city},{state_code},{country_code}"
    elif country_code:
        q = f"{city},{country_code}"

    params = {"q": q, "limit": 5}

    try:
        data = await make_weather_request(url, params)
        if data and len(data) > 0:
            # Cast data to list to satisfy mypy
            data_list = cast(list[dict[str, Any]], data)
            lat = float(data_list[0].get("lat", 0))
            lon = float(data_list[0].get("lon", 0))
            return lat, lon
    except Exception as e:
        print(f"Error getting coordinates: {str(e)}")

    # If direct geocoding fails, try with zip code (if the city looks like a zip code)
    if city.isdigit() or (len(city) > 3 and city[0:3].isalpha() and city[3:].isdigit()):
        url = "http://api.openweathermap.org/geo/1.0/zip"
        params = {"zip": f"{city},{country_code}" if country_code else city}

        try:
            zip_data = await make_weather_request(url, params)
            if zip_data and "lat" in zip_data and "lon" in zip_data:
                lat = float(zip_data.get("lat", 0))
                lon = float(zip_data.get("lon", 0))
                return lat, lon
        except Exception as e:
            print(f"Error getting coordinates from zip: {str(e)}")

    # If all else fails, try OpenStreetMap Nominatim as a fallback
    url = "https://nominatim.openstreetmap.org/search"
    q = f"{city}"
    if state_code:
        q += f", {state_code}"
    if country_code:
        q += f", {country_code}"

    params = {
        "q": q,
        "format": "json",
        "limit": 1,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Cast data to list to satisfy mypy
                    data_list = cast(list[dict[str, Any]], data)
                    lat = float(data_list[0].get("lat", 0))
                    lon = float(data_list[0].get("lon", 0))
                    return lat, lon
    except Exception as e:
        print(f"Error with Nominatim fallback: {str(e)}")

    return None


def format_alert(alert: dict) -> str:
    """Format a weather alert for display."""
    event = alert.get("event", "Unknown")
    sender = alert.get("sender_name", "Unknown")
    start = alert.get("start", "Unknown")
    end = alert.get("end", "Unknown")
    description = alert.get("description", "No description available")

    return f"\nEvent: {event}\nSender: {sender}\nStart: {start}\nEnd: {end}\nDescription: {description}\n"


def kelvin_to_unit(temp: float, unit: str) -> float:
    """Convert temperature from Kelvin to the specified unit."""
    if unit == "celsius":
        return temp - 273.15
    elif unit == "fahrenheit":
        return (temp - 273.15) * 9 / 5 + 32
    else:
        return temp  # Return Kelvin if unit is not recognized


def format_temperature(temp: float, unit: str) -> str:
    """Format temperature with the appropriate unit symbol."""
    if unit == "celsius":
        return f"{round(temp, 1)}°C"
    elif unit == "fahrenheit":
        return f"{round(temp, 1)}°F"
    else:
        return f"{round(temp, 1)}K"


@mcp.tool()
async def get_user_location() -> str:
    """Get your current location based on IP address."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://ipinfo.io/json")
            if response.status_code == 200:
                data = response.json()
                city = data.get("city", "Unknown")
                region = data.get("region", "")
                country = data.get("country", "Unknown")
                loc = data.get("loc", "")

                location_str = f"{city}"
                if region:
                    location_str += f", {region}"
                location_str += f", {country}"

                if loc:
                    lat, lon = loc.split(",")
                    return f"Your location: {location_str} (Coordinates: {lat}, {lon})"
                else:
                    return f"Your location: {location_str} (Coordinates unavailable)"
            else:
                return "Your location: Unknown (Coordinates unavailable)"
    except Exception as e:
        print(f"Error getting location: {str(e)}")
        return "Could not determine your location due to an error."


@mcp.tool()
async def get_weather_by_coordinates(
    latitude: float, longitude: float, units: Literal["celsius", "fahrenheit"] = "celsius"
) -> str:
    """Get current weather conditions for the specified coordinates."""
    # Try One Call API 3.0 first
    url = OPENWEATHER_API_BASE
    params = {
        "lat": latitude,
        "lon": longitude,
        "exclude": "minutely,hourly,daily,alerts",
    }

    data = await make_weather_request(url, params)

    # If One Call API 3.0 fails, fall back to the regular API
    if not data or "current" not in data:
        print("Falling back to API 2.5 due to missing data in API 3.0 response")
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
        }
        data = await make_weather_request(url, params)

    if not data:
        return f"Could not retrieve weather data for coordinates ({latitude}, {longitude})."

    # Process data from One Call API 3.0
    if "current" in data:
        current = data["current"]
        temp = current.get("temp", 273.15)  # Default to 0°C if temp is missing
        feels_like = current.get("feels_like", temp)
        humidity = current.get("humidity", 0)
        wind_speed = current.get("wind_speed", 0)
        wind_deg = current.get("wind_deg", 0)
        weather = current.get("weather", [{}])[0]
        description = weather.get("description", "Unknown")

        # Get the location name if available
        location_name = data.get("name", f"coordinates ({latitude}, {longitude})")

        # Format the response
        response = f"Current Weather for {location_name}:\n"

        # Convert temperatures from Kelvin to the requested unit
        temp_converted = kelvin_to_unit(temp, units)
        feels_like_converted = kelvin_to_unit(feels_like, units)

        response += f"Temperature: {format_temperature(temp_converted, units)}\n"
        response += f"Feels Like: {format_temperature(feels_like_converted, units)}\n"
        response += f"Conditions: {description.capitalize()}\n"
        response += f"Humidity: {humidity}%\n"

        # Convert wind direction to cardinal direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        direction_index = round(wind_deg / 45) % 8
        wind_direction = directions[direction_index]

        response += f"Wind: {round(wind_speed, 1)} m/s {wind_direction}\n"

        # Add alerts if available
        if "alerts" in data and data["alerts"]:
            response += "\nWeather Alerts:\n"
            for alert in data["alerts"]:
                response += format_alert(alert)

        return response

    # Process data from API 2.5 (fallback)
    else:
        main = data.get("main", {})
        temp = main.get("temp", 273.15)
        feels_like = main.get("feels_like", temp)
        humidity = main.get("humidity", 0)

        wind = data.get("wind", {})
        wind_speed = wind.get("speed", 0)
        wind_deg = wind.get("deg", 0)

        weather = data.get("weather", [{}])[0]
        description = weather.get("description", "Unknown")

        location_name = data.get("name", f"coordinates ({latitude}, {longitude})")

        # Format the response
        response = f"Current Weather for {location_name}:\n"

        # Convert temperatures from Kelvin to the requested unit
        temp_converted = kelvin_to_unit(temp, units)
        feels_like_converted = kelvin_to_unit(feels_like, units)

        response += f"Temperature: {format_temperature(temp_converted, units)}\n"
        response += f"Feels Like: {format_temperature(feels_like_converted, units)}\n"
        response += f"Conditions: {description.capitalize()}\n"
        response += f"Humidity: {humidity}%\n"

        # Convert wind direction to cardinal direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        direction_index = round(wind_deg / 45) % 8
        wind_direction = directions[direction_index]

        response += f"Wind: {round(wind_speed, 1)} m/s {wind_direction}\n"

        return response


@mcp.tool()
async def get_alerts(city: str, country_code: str = "", state_code: str = "") -> str:
    """Get weather alerts for a location."""
    # Get coordinates for the location
    coordinates = await get_coordinates(city, country_code, state_code)
    if not coordinates:
        location_str = f"{city}, {country_code if country_code else ''}"
        if state_code:
            location_str += f", {state_code}"
        return (
            f"Unable to find coordinates for {location_str}. "
            f"Try providing a larger nearby city, postal code, or use coordinates directly."
        )

    lat, lon = coordinates

    # Get weather data
    url = OPENWEATHER_API_BASE
    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,hourly,daily",
    }

    data = await make_weather_request(url, params)
    if not data:
        location_str = f"{city}, {country_code if country_code else ''}"
        if state_code:
            location_str += f", {state_code}"
        return f"Could not retrieve weather data for {location_str}."

    if "alerts" not in data or not data["alerts"]:
        location_str = f"{city}, {country_code if country_code else ''}"
        if state_code:
            location_str += f", {state_code}"
        return f"No active alerts for {location_str}."

    formatted_alerts = [format_alert(alert) for alert in data["alerts"]]
    return "".join(formatted_alerts)


@mcp.tool()
async def get_forecast(
    city: str,
    country_code: str = "",
    state_code: str = "",
    units: Literal["celsius", "fahrenheit"] = "celsius",
    days: int = 5,
) -> str:
    """Get daily weather forecast for a location."""
    # Get coordinates for the location
    coordinates = await get_coordinates(city, country_code, state_code)
    if not coordinates:
        location_str = f"{city}, {country_code if country_code else ''}"
        if state_code:
            location_str += f", {state_code}"
        return (
            f"Unable to find coordinates for {location_str}. "
            f"Try providing a larger nearby city, postal code, or use coordinates directly."
        )

    lat, lon = coordinates

    # Get weather data
    url = OPENWEATHER_API_BASE
    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,hourly,current",
    }

    data = await make_weather_request(url, params)
    if not data:
        location_str = f"{city}, {country_code if country_code else ''}"
        if state_code:
            location_str += f", {state_code}"
        return f"Could not retrieve forecast data for {location_str}."

    # Format the forecast
    location_str = f"{city}, {country_code if country_code else ''}"
    if state_code:
        location_str += f", {state_code}"
    response = f"Weather Forecast for {location_str}\n"
    response += "---\n\n"

    if "daily" not in data or not data["daily"]:
        return response + "No forecast data available."

    # Limit the number of days
    days_to_show = min(days, len(data["daily"]))

    for i in range(days_to_show):
        day = data["daily"][i]
        date = day.get("dt", 0)

        # Convert Unix timestamp to date
        from datetime import datetime

        date_str = datetime.fromtimestamp(date).strftime("%Y-%m-%d")

        temp = day.get("temp", {})
        day_temp = temp.get("day", 273.15)
        min_temp = temp.get("min", 273.15)
        max_temp = temp.get("max", 273.15)

        humidity = day.get("humidity", 0)
        wind_speed = day.get("wind_speed", 0)
        wind_deg = day.get("wind_deg", 0)

        weather = day.get("weather", [{}])[0]
        description = weather.get("description", "Unknown")

        pop = day.get("pop", 0) * 100  # Probability of precipitation (0-1)

        # Format the day's forecast
        response += f"{date_str}:\n"
        temp_str = format_temperature(day_temp, units)
        min_temp_str = format_temperature(min_temp, units)
        max_temp_str = format_temperature(max_temp, units)
        response += f"Temperature: {temp_str} (Min: {min_temp_str}, Max: {max_temp_str})\n"
        response += f"Conditions: {description.capitalize()}\n"
        response += f"Humidity: {humidity}%\n"

        # Convert wind direction to cardinal direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        direction_index = round(wind_deg / 45) % 8
        wind_direction = directions[direction_index]

        response += f"Wind Speed: {round(wind_speed, 1)} m/s {wind_direction}\n"
        response += f"Chance of Rain: {round(pop)}%\n"

        if i < days_to_show - 1:
            response += "\n"

    return response


@mcp.tool()
async def get_current_weather(
    city: str, country_code: str = "", state_code: str = "", units: Literal["celsius", "fahrenheit"] = "celsius"
) -> str:
    """Get current weather conditions for a location."""
    # Get coordinates for the location
    coordinates = await get_coordinates(city, country_code, state_code)
    if not coordinates:
        location_str = f"{city}, {country_code if country_code else ''}"
        if state_code:
            location_str += f", {state_code}"
        return (
            f"Unable to find coordinates for {location_str}. "
            f"Try providing a larger nearby city, postal code, or use coordinates directly."
        )

    lat, lon = coordinates

    # Get weather data
    result = await get_weather_by_coordinates(lat, lon, units)

    # Replace the generic location with the specific city name
    location_str = f"{city}, {country_code if country_code else ''}"
    if state_code:
        location_str += f", {state_code}"

    # Replace the first line with the city name
    lines = result.split("\n")
    lines[0] = f"Current Weather for {location_str}:"

    return "\n".join(lines)


@mcp.tool()
async def get_hourly_forecast(
    city: str,
    country_code: str = "",
    state_code: str = "",
    units: Literal["celsius", "fahrenheit"] = "celsius",
    hours: int = 24,
) -> str:
    """Get hourly weather forecast for a location."""
    # Get coordinates for the location
    coordinates = await get_coordinates(city, country_code, state_code)
    if not coordinates:
        location_str = f"{city}, {country_code if country_code else ''}"
        if state_code:
            location_str += f", {state_code}"
        return (
            f"Unable to find coordinates for {location_str}. "
            f"Try providing a larger nearby city, postal code, or use coordinates directly."
        )

    lat, lon = coordinates

    # Get weather data from One Call API 3.0
    url = OPENWEATHER_API_BASE
    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,daily,current",
    }

    data = await make_weather_request(url, params)

    # Format the location string for output
    location_str = f"{city}, {country_code if country_code else ''}"
    if state_code:
        location_str += f", {state_code}"
    response = f"Hourly Weather Forecast for {location_str}\n"

    # Check if we got valid data from One Call API 3.0
    if not data or "hourly" not in data or not data["hourly"]:
        # Try fallback to 5-day/3-hour forecast API if One Call API 3.0 fails
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": lat,
            "lon": lon,
        }

        data = await make_weather_request(url, params)

        if not data or "list" not in data or not data["list"]:
            return response + "No hourly forecast data available."

        # Process data from 5-day/3-hour forecast API
        forecast_list = data["list"]
        hours_to_show = min(hours, len(forecast_list))

        for i in range(hours_to_show):
            hour = forecast_list[i]
            time = hour.get("dt", 0)

            # Convert Unix timestamp to time
            from datetime import datetime

            time_str = datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M")

            main = hour.get("main", {})
            temp = main.get("temp", 273.15)
            weather = hour.get("weather", [{}])[0]
            description = weather.get("description", "Unknown")

            wind = hour.get("wind", {})
            wind_speed = wind.get("speed", 0)
            wind_deg = wind.get("deg", 0)

            pop = hour.get("pop", 0) * 100  # Probability of precipitation (0-1)

            # Convert wind direction to cardinal direction
            directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
            direction_index = round(wind_deg / 45) % 8
            wind_direction = directions[direction_index]

            # Convert temperature from Kelvin to the requested unit
            temp_converted = kelvin_to_unit(temp, units)

            # Format the hour's forecast
            forecast_parts = [
                f"{time_str}: {format_temperature(temp_converted, units)}",
                f"{description.capitalize()}",
                f"Wind: {round(wind_speed, 1)} m/s {wind_direction}",
                f"Chance of Rain: {round(pop)}%",
            ]
            response += ", ".join(forecast_parts) + "\n"

        return response

    # Process data from One Call API 3.0
    hours_to_show = min(hours, len(data["hourly"]))

    for i in range(hours_to_show):
        hour = data["hourly"][i]
        time = hour.get("dt", 0)

        # Convert Unix timestamp to time
        from datetime import datetime

        time_str = datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M")

        temp = hour.get("temp", 273.15)
        weather = hour.get("weather", [{}])[0]
        description = weather.get("description", "Unknown")

        wind_speed = hour.get("wind_speed", 0)
        wind_deg = hour.get("wind_deg", 0)

        pop = hour.get("pop", 0) * 100  # Probability of precipitation (0-1)

        # Convert wind direction to cardinal direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        direction_index = round(wind_deg / 45) % 8
        wind_direction = directions[direction_index]

        # Convert temperature from Kelvin to the requested unit
        temp_converted = kelvin_to_unit(temp, units)

        # Format the hour's forecast
        forecast_parts = [
            f"{time_str}: {format_temperature(temp_converted, units)}",
            f"{description.capitalize()}",
            f"Wind: {round(wind_speed, 1)} m/s {wind_direction}",
            f"Chance of Rain: {round(pop)}%",
        ]
        response += ", ".join(forecast_parts) + "\n"

    return response


@mcp.tool()
async def test_api_connection() -> str:
    """Test the connection to the OpenWeatherMap API."""
    print("DEBUG: Testing API connection")

    # Test with Madrid coordinates (known to work)
    test_lat, test_lon = 40.4165, -3.7026

    url = OPENWEATHER_API_BASE
    params = {
        "lat": test_lat,
        "lon": test_lon,
        "exclude": "minutely,hourly,daily,alerts",
    }

    print(f"DEBUG: Testing with URL: {url}")
    print(f"DEBUG: Testing with params: {params}")

    # For debugging, show what the full URL would look like
    debug_url = f"{url}?lat={test_lat}&lon={test_lon}&exclude=minutely,hourly,daily,alerts&appid=YOUR_API_KEY"
    print(f"DEBUG: Full request URL would be: {debug_url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30.0)

            print(f"DEBUG: Response status code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"DEBUG: Response data keys: {list(data.keys())}")

                if "current" in data:
                    temp_kelvin = data["current"].get("temp")
                    print(f"DEBUG: Current temperature in Kelvin: {temp_kelvin}")

                    temp_celsius = kelvin_to_unit(temp_kelvin, "celsius")
                    return f"API test successful! Current temperature in Madrid is {round(temp_celsius, 1)}°C"
                else:
                    return f"API response received but missing 'current' data. Response keys: {list(data.keys())}"
            else:
                return f"API request failed with status code: {response.status_code}. Response: {response.text}"
    except Exception as e:
        return f"API connection test failed with error: {str(e)}"


@mcp.tool()
async def check_api_key_and_subscription() -> str:
    """Check if your API key is valid and if you have an active One Call subscription."""
    print("DEBUG: Checking API key and subscription")

    # First, test the regular API (which works with any valid API key)
    print("DEBUG: Testing regular API access")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": "London,GB",
        "appid": OPENWEATHER_API_KEY,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30.0)

            print(f"DEBUG: Regular API response status code: {response.status_code}")

            if response.status_code != 200:
                error_msg = (
                    f"API key may be invalid. Regular API request failed with status code: {response.status_code}."
                )
                error_msg += f" Response: {response.text}"
                return error_msg

            print("DEBUG: Regular API access successful - API key is valid")

            # Now test the One Call API 3.0 (which requires a subscription)
            print("DEBUG: Testing One Call API 3.0 access")

            # Use London coordinates for testing
            london_lat, london_lon = 51.5074, -0.1278

            one_call_url = OPENWEATHER_API_BASE
            one_call_params = {
                "lat": london_lat,
                "lon": london_lon,
                "exclude": "minutely,hourly,daily,alerts",
                "appid": OPENWEATHER_API_KEY,
            }

            one_call_response = await client.get(
                one_call_url, params=one_call_params, headers={"User-Agent": USER_AGENT}, timeout=30.0
            )

            print(f"DEBUG: One Call API 3.0 response status code: {one_call_response.status_code}")

            if one_call_response.status_code == 200:
                data = one_call_response.json()

                if "current" in data:
                    return "API key is valid and One Call API 3.0 subscription is active!"
                else:
                    data_keys = list(data.keys())
                    return (
                        f"API key is valid but One Call API 3.0 response is missing 'current' data. "
                        f"Response keys: {data_keys}"
                    )
            elif one_call_response.status_code == 401:
                return (
                    "API key is valid but One Call API 3.0 subscription is not active. "
                    "You need to subscribe to the 'One Call by Call' subscription plan."
                )
            elif one_call_response.status_code == 429:
                return "API key is valid but you've exceeded your One Call API 3.0 quota."
            else:
                error_msg = f"One Call API 3.0 request failed with status code: {one_call_response.status_code}."
                error_msg += f" Response: {one_call_response.text}"
                return error_msg
    except Exception as e:
        return f"Error testing One Call API 3.0: {str(e)}"


if __name__ == "__main__":
    mcp.run()