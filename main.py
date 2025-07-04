#!/usr/bin/env python3
"""
Weather MCP Server using WeatherAPI.com
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from fastapi import HTTPException

# Load environment variables
load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Create MCP server
mcp = FastMCP(
    name="WeatherMCP",
    prompt="Weather server providing current conditions, forecasts, air quality, and astronomy data via WeatherAPI.com"
)

# WeatherAPI base configuration
WEATHER_BASE_URL = "https://api.weatherapi.com/v1"


def validate_date(date_str: str) -> None:
    """Validate date string format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


async def fetch_weather_data(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch data from WeatherAPI with error handling"""
    if not WEATHER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="WEATHER_API_KEY not found in environment variables"
        )
    
    params["key"] = WEATHER_API_KEY
    url = f"{WEATHER_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                raise HTTPException(status_code=response.status_code, detail=error_msg)
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


@mcp.tool()
async def get_current_weather(
    location: str,
    include_air_quality: bool = False
) -> Dict[str, Any]:
    """
    Get current weather conditions for a location.
    
    Args:
        location: City name, coordinates (lat,lon), IP address, or postcode
        include_air_quality: Include air quality data in response
    
    Returns:
        Current weather data including temperature, conditions, wind, etc.
    """
    params = {
        "q": location,
        "aqi": "yes" if include_air_quality else "no"
    }
    return await fetch_weather_data("current.json", params)


@mcp.tool()
async def get_weather_forecast(
    location: str,
    days: int = 3,
    include_air_quality: bool = False,
    include_alerts: bool = False
) -> Dict[str, Any]:
    """
    Get weather forecast for a location.
    
    Args:
        location: City name, coordinates (lat,lon), IP address, or postcode
        days: Number of forecast days (1-14)
        include_air_quality: Include air quality data
        include_alerts: Include weather alerts
    
    Returns:
        Weather forecast data for specified days
    """
    if not 1 <= days <= 14:
        raise HTTPException(
            status_code=400,
            detail="Days must be between 1 and 14"
        )
    
    params = {
        "q": location,
        "days": days,
        "aqi": "yes" if include_air_quality else "no",
        "alerts": "yes" if include_alerts else "no"
    }
    return await fetch_weather_data("forecast.json", params)


@mcp.tool()
async def get_weather_history(
    location: str,
    date: str
) -> Dict[str, Any]:
    """
    Get historical weather data for a specific date.
    
    Args:
        location: City name, coordinates (lat,lon), IP address, or postcode
        date: Date in YYYY-MM-DD format
    
    Returns:
        Historical weather data for the specified date
    """
    validate_date(date)
    
    params = {
        "q": location,
        "dt": date
    }
    return await fetch_weather_data("history.json", params)


@mcp.tool()
async def get_air_quality(location: str) -> Dict[str, Any]:
    """
    Get current air quality data for a location.
    
    Args:
        location: City name, coordinates (lat,lon), IP address, or postcode
    
    Returns:
        Air quality data including pollutant levels and indices
    """
    params = {
        "q": location,
        "aqi": "yes"
    }
    return await fetch_weather_data("current.json", params)


@mcp.tool()
async def get_astronomy_data(
    location: str,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get astronomy data (sunrise, sunset, moon phases) for a location.
    
    Args:
        location: City name, coordinates (lat,lon), IP address, or postcode
        date: Date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Astronomy data including sunrise, sunset, moonrise, moonset, and moon phase
    """
    if date:
        validate_date(date)
    else:
        date = datetime.now().strftime("%Y-%m-%d")
    
    params = {
        "q": location,
        "dt": date
    }
    return await fetch_weather_data("astronomy.json", params)


@mcp.tool()
async def search_locations(query: str) -> Dict[str, Any]:
    """
    Search for locations matching a query.
    
    Args:
        query: Search query (city name, postcode, etc.)
    
    Returns:
        List of matching locations with names, regions, countries, and coordinates
    """
    params = {"q": query}
    return await fetch_weather_data("search.json", params)


@mcp.tool()
async def get_weather_alerts(location: str) -> Dict[str, Any]:
    """
    Get weather alerts and warnings for a location.
    
    Args:
        location: City name, coordinates (lat,lon), IP address, or postcode
    
    Returns:
        Weather alerts and warnings if any are active
    """
    params = {
        "q": location,
        "alerts": "yes"
    }
    data = await fetch_weather_data("forecast.json", params)
    return {"alerts": data.get("alerts", {"alert": []})}


@mcp.tool()
async def get_timezone_info(location: str) -> Dict[str, Any]:
    """
    Get timezone information for a location.
    
    Args:
        location: City name, coordinates (lat,lon), IP address, or postcode
    
    Returns:
        Timezone information including name, offset, and local time
    """
    params = {"q": location}
    return await fetch_weather_data("timezone.json", params)


@mcp.tool()
async def get_marine_weather(
    location: str,
    days: int = 1
) -> Dict[str, Any]:
    """
    Get marine weather data for coastal locations.
    
    Args:
        location: Coastal city or coordinates
        days: Number of forecast days (1-7)
    
    Returns:
        Marine weather data including wave height, tide times, etc.
    """
    if not 1 <= days <= 7:
        raise HTTPException(
            status_code=400,
            detail="Days must be between 1 and 7 for marine weather"
        )
    
    params = {
        "q": location,
        "days": days
    }
    return await fetch_weather_data("marine.json", params)


@mcp.tool()
async def get_sports_data(location: str) -> Dict[str, Any]:
    """
    Get sports events and weather conditions for a location.
    
    Args:
        location: City name, coordinates (lat,lon), IP address, or postcode
    
    Returns:
        Sports events with weather conditions
    """
    params = {"q": location}
    return await fetch_weather_data("sports.json", params)


if __name__ == "__main__":
    mcp.run()