#!/usr/bin/env python3
"""
Working SSE Server for Weather MCP using manual implementation
"""
import asyncio
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

# Import weather functions directly
from main import (
    get_current_weather,
    get_weather_forecast,
    get_weather_history,
    get_air_quality,
    get_astronomy_data,
    get_weather_alerts,
    search_locations,
    get_timezone_info
)

load_dotenv()

app = FastAPI(title="Weather MCP SSE Server")

# Tool registry
TOOLS = {
    "get_current_weather": get_current_weather,
    "get_weather_forecast": get_weather_forecast,
    "get_weather_history": get_weather_history, 
    "get_air_quality": get_air_quality,
    "get_astronomy_data": get_astronomy_data,
    "get_weather_alerts": get_weather_alerts,
    "search_locations": search_locations,
    "get_timezone_info": get_timezone_info
}

# Store active connections
connections = {}

@app.get("/")
async def root():
    return {
        "name": "Weather MCP SSE Server",
        "version": "1.0.0",
        "endpoints": {
            "sse": "/sse",
            "message": "/message",
            "tools": list(TOOLS.keys())
        }
    }

@app.post("/sse")
async def sse_endpoint(request: Request):
    """Handle MCP initialization via POST"""
    try:
        # Read the request body
        body = await request.body()
        if body:
            message = json.loads(body.decode())
        else:
            # If no body, treat as initialization request
            message = {"method": "initialize", "id": 1}
        
        # Handle initialization
        if message.get("method") == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": message.get("id", 1),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "WeatherMCP",
                        "version": "1.0.0"
                    }
                }
            }
            return response
        else:
            # Handle other methods directly
            method = message.get("method")
            msg_id = message.get("id")
            params = message.get("params", {})
            
            if method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [
                            {
                                "name": name,
                                "description": func.__doc__ or f"Weather tool: {name}",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                            for name, func in TOOLS.items()
                        ]
                    }
                }
                
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name not in TOOLS:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    }
                else:
                    try:
                        result = await TOOLS[tool_name](**tool_args)
                        response = {
                            "jsonrpc": "2.0",
                            "id": msg_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(result)
                                    }
                                ]
                            }
                        }
                    except Exception as e:
                        response = {
                            "jsonrpc": "2.0",
                            "id": msg_id,
                            "error": {
                                "code": -32603,
                                "message": str(e)
                            }
                        }
            else:
                response = {
                    "jsonrpc": "2.0", 
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return response
            
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }

@app.post("/message")
async def message_endpoint(request: Request):
    """Handle MCP messages via POST"""
    
    try:
        message = await request.json()
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})
        
        if method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": name,
                            "description": func.__doc__ or f"Weather tool: {name}",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                        for name, func in TOOLS.items()
                    ]
                }
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name not in TOOLS:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
            else:
                try:
                    result = await TOOLS[tool_name](**tool_args)
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result)
                                }
                            ]
                        }
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
        else:
            response = {
                "jsonrpc": "2.0", 
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        # Send response to all SSE connections
        for connection_queue in connections.values():
            try:
                connection_queue.put_nowait(response)
            except:
                pass
                
        return response
        
    except Exception as e:
        error_response = {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }
        
        # Send error to all connections
        for connection_queue in connections.values():
            try:
                connection_queue.put_nowait(error_response)
            except:
                pass
                
        return error_response

if __name__ == "__main__":
    print("Starting Weather MCP SSE Server...")
    print("SSE endpoint: https://localhost:8001/sse")
    print("Message endpoint: https://localhost:8001/message")
    print("Set WEATHER_API_KEY environment variable before testing")
    
    # uvicorn.run(
    #     "working_sse_server:app",
    #     host="0.0.0.0",
    #     port=8001,
    #     reload=False,
    #     ssl_keyfile="server.key",
    #     ssl_certfile="server.crt"
    # )
    
    uvicorn.run(
        "sse_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        # ssl_keyfile="server.key",
        # ssl_certfile="server.crt"
    )