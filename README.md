# Weather MCP Server

A Model Context Protocol (MCP) server that provides comprehensive weather data using [WeatherAPI.com](https://www.weatherapi.com/). This server offers current weather conditions, forecasts, historical data, air quality information, astronomy data, and more.

## Features

- 🌤️ **Current Weather** - Real-time weather conditions
- 📅 **Weather Forecasts** - Up to 14-day forecasts
- 📊 **Historical Data** - Past weather information
- 🌬️ **Air Quality** - Air pollution and quality indices
- 🌙 **Astronomy** - Sunrise, sunset, moon phases
- 🚨 **Weather Alerts** - Severe weather warnings
- 🗺️ **Location Search** - Find locations worldwide
- 🌊 **Marine Weather** - Coastal and marine conditions
- ⚽ **Sports Data** - Weather for sporting events
- 🕐 **Timezone Info** - Local time and timezone data

## Installation

### Docker
```bash
docker build . -t sse_weather_server
docker run -p 8001:8001 -e WEATHER_API_KEY=xxxx sse_weather_server
```
### Directly on your machine

1. **Clone or create the project:**
   ```bash
   mkdir weather-mcp-server
   cd weather-mcp-server
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get WeatherAPI key:**
   - Sign up at [WeatherAPI.com](https://www.weatherapi.com/signup.aspx)
   - Copy your API key

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API key
   ```

## Configuration

Create a `.env` file with your WeatherAPI key:

```env
WEATHER_API_KEY=your_actual_api_key_here
LOG_LEVEL=INFO
```

## Usage

The same MCP server (defined in `main.py`) can be run over three different
transports depending on how your client connects.

### SSE transport (HTTP, port 8001)

```bash
python server_sse.py
```

This is the transport used by the Docker image.

### Streamable HTTP transport (port 8002)

```bash
python server_streamable.py
```

### stdio transport (local)

```bash
python main.py
```

### Testing the SSE server

With the SSE server running on port 8001, you can exercise it with the bundled
test client:

```bash
python client.py
```

### Available Tools

#### Weather Data
- `get_current_weather(location, include_air_quality=False)` - Current conditions
- `get_weather_forecast(location, days=3, include_air_quality=False, include_alerts=False)` - Multi-day forecast
- `get_weather_history(location, date)` - Historical weather data
- `get_air_quality(location)` - Air quality information

#### Astronomy & Environment
- `get_astronomy_data(location, date=None)` - Sun/moon data
- `get_marine_weather(location, days=1)` - Marine conditions
- `get_weather_alerts(location)` - Severe weather warnings

#### Location & Info
- `search_locations(query)` - Find locations
- `get_timezone_info(location)` - Timezone information
- `get_sports_data(location)` - Sports events weather
