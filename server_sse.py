#!/usr/bin/env python3
"""
SSE Server for Weather MCP
Uses the MCP SDK's built-in SSE transport.
"""
from main import mcp

if __name__ == "__main__":
    mcp.settings.port = 8001
    mcp.run(transport="sse")
