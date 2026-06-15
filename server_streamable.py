#!/usr/bin/env python3
"""
Streamable HTTP Server for Weather MCP
Uses the MCP SDK's built-in streamable HTTP transport instead of SSE.
"""
from main import mcp

if __name__ == "__main__":
    mcp.settings.port = 8002
    mcp.run(transport="streamable-http")
