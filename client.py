#!/usr/bin/env python3
"""
Working test client that mimics MCP ClientSession without SSE client library
"""
import asyncio
import json
import httpx

class MockMCPSession:
    """Mock MCP session that works with our SSE server"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = None
        self.message_id = 0
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(verify=False)
        # Initialize the MCP connection
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def _next_id(self):
        self.message_id += 1
        return self.message_id
    
    async def _initialize(self):
        """Initialize MCP connection"""
        message = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "TestClient",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self.client.post(f"{self.base_url}/sse", json=message)
        result = response.json()
        
        if 'error' in result:
            raise Exception(f"Initialization failed: {result['error']}")
        
        print(f"Connected to MCP server: {result['result']['serverInfo']['name']}")
        return result
    
    async def list_tools(self):
        """List available tools"""
        message = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list"
        }
        
        response = await self.client.post(f"{self.base_url}/sse", json=message)
        result = response.json()
        
        if 'result' in result:
            # Create mock tools object
            class MockTools:
                def __init__(self, tools_data):
                    self.tools = [MockTool(tool) for tool in tools_data]
            
            class MockTool:
                def __init__(self, tool_data):
                    self.name = tool_data['name']
                    self.description = tool_data['description']
            
            return MockTools(result['result']['tools'])
        else:
            raise Exception(f"Error listing tools: {result}")
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool"""
        message = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self.client.post(f"{self.base_url}/sse", json=message)
        result = response.json()
        
        if 'result' in result:
            # Create mock result object
            class MockResult:
                def __init__(self, result_data):
                    self.content = [MockContent(content) for content in result_data['content']]
            
            class MockContent:
                def __init__(self, content_data):
                    self.text = content_data['text']
            
            return MockResult(result['result'])
        else:
            raise Exception(f"Error calling tool {tool_name}: {result}")

async def test_weather_server():
    """Test the weather MCP server using our mock session"""
    print("=== Testing Weather MCP Server via SSE ===")
    
    async with MockMCPSession("http://localhost:8001") as session:
        # List available tools
        print("=== Available Tools ===")
        tools = await session.list_tools()
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")
        
        print("\n=== Current Weather for London ===")
        result = await session.call_tool("get_current_weather", {
            "location": "London",
            "include_air_quality": True
        })
        weather_data = json.loads(result.content[0].text)
        
        # Pretty print weather data
        location = weather_data['location']
        current = weather_data['current']
        
        print(f"Location: {location['name']}, {location['country']}")
        print(f"Temperature: {current['temp_c']}°C ({current['temp_f']}°F)")
        print(f"Condition: {current['condition']['text']}")
        print(f"Humidity: {current['humidity']}%")
        print(f"Wind: {current['wind_kph']} km/h")
        
        if 'air_quality' in weather_data:
            aqi = weather_data['air_quality']
            print(f"Air Quality Index: {aqi.get('us-epa-index', 'N/A')}")
        
        print("\n=== 3-Day Forecast for Tokyo ===")
        forecast_result = await session.call_tool("get_weather_forecast", {
            "location": "Tokyo", 
            "days": 3,
            "include_air_quality": False
        })
        forecast_data = json.loads(forecast_result.content[0].text)
        
        for day in forecast_data['forecast']['forecastday']:
            date = day['date']
            day_weather = day['day']
            print(f"{date}: {day_weather['condition']['text']}")
            print(f"  High: {day_weather['maxtemp_c']}°C, Low: {day_weather['mintemp_c']}°C")

        print("\n=== Search Locations ===")
        search_result = await session.call_tool("search_locations", {
            "query": "Paris"
        })
        search_data = json.loads(search_result.content[0].text)
        
        for i, location in enumerate(search_data[:3], 1):
            print(f"{i}. {location['name']}, {location['region']}, {location['country']}")

if __name__ == "__main__":
    asyncio.run(test_weather_server())