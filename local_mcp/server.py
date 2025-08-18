# server.py
"""
This script implements an MCP (Model-Context-Protocol) server.

The server exposes a set of tools for interacting with a local SQLite database.
It listens for tool calls from an MCP client (ADK Agent), executes
the corresponding database operations, and returns the results.

The server is designed to be run as a standalone process, communicating with
the client over standard input/output (stdio).
"""

import sys
from pathlib import Path

# Setting absolute path for imports to work when ADK Agent runs the server.py directly
sys.path.insert(0, str((Path(__file__).parent / "..").resolve()))

import asyncio
import json

import mcp.server.stdio
from dotenv import load_dotenv

# ADK Tool Imports
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

# MCP Server Imports
from mcp import types as mcp_types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Local Imports
from local_mcp.create_db import create_database
from local_mcp.db_utils import (
    delete_data,
    get_table_schema,
    insert_data,
    list_db_tables,
    query_db_table,
)
from local_mcp.logger import logger

# --- Load Environment Variables ---
load_dotenv()

# --- Create database ---
create_database()


# --- MCP Server Setup ---
logger.info("Creating MCP Server instance for SQLite DB...")
app = Server("sqlite-db-mcp-server")

# Wrap database utility functions as ADK FunctionTools
ADK_DB_TOOLS = {
    "list_db_tables": FunctionTool(func=list_db_tables),
    "get_table_schema": FunctionTool(func=get_table_schema),
    "query_db_table": FunctionTool(func=query_db_table),
    "insert_data": FunctionTool(func=insert_data),
    "delete_data": FunctionTool(func=delete_data),
}


# --- MCP Server Handlers ---
@app.list_tools()
async def list_mcp_tools() -> list[mcp_types.Tool]:
    """MCP handler to list tools this server exposes.

    This function is called by the MCP client(ADK Agent) to discover the available
    tools. It converts the ADK FunctionTools into the MCP Tool format.

    Returns:
        A list of mcp_types.Tool objects representing the available tools.
    """
    logger.info("MCP Server: Received list_tools request.")
    mcp_tools_list = []
    for tool_name, adk_tool_instance in ADK_DB_TOOLS.items():
        if not adk_tool_instance.name:
            adk_tool_instance.name = tool_name

        mcp_tool_schema = adk_to_mcp_tool_type(adk_tool_instance)
        logger.info(
            f"MCP Server: Advertising tool: {mcp_tool_schema.name}, InputSchema: {mcp_tool_schema.inputSchema}"
        )
        mcp_tools_list.append(mcp_tool_schema)
    return mcp_tools_list


# --- MCP Server Handlers ---
@app.call_tool()
async def call_mcp_tool(name: str, arguments: dict) -> list[mcp_types.TextContent]:
    """MCP handler to execute a tool call requested by an MCP client(ADK Agent).

    This function receives a tool name and arguments, executes the corresponding
    ADK FunctionTool, and returns the result as a JSON-formatted string.

    Args:
        name: The name of the tool to execute.
        arguments: A dictionary of arguments for the tool.

    Returns:
        A list containing a single TextContent object with the tool's
        output serialized as a JSON string. If an error occurs, the JSON
        will contain an error message.
    """
    logger.info(
        f"MCP Server: Received call_tool request for '{name}' with args: {arguments}"
    )

    if name in ADK_DB_TOOLS:
        adk_tool_instance = ADK_DB_TOOLS[name]
        try:
            adk_tool_response = await adk_tool_instance.run_async(
                args=arguments,
                tool_context=None,  # type: ignore
            )
            logger.info(
                f"MCP Server: ADK tool '{name}' executed. Response: {adk_tool_response}"
            )
            response_text = json.dumps(adk_tool_response, indent=2)
            return [mcp_types.TextContent(type="text", text=response_text)]

        except Exception as e:
            logger.error(
                f"MCP Server: Error executing ADK tool '{name}': {e}", exc_info=True
            )
            error_payload = {
                "success": False,
                "message": f"Failed to execute tool '{name}': {str(e)}",
            }
            error_text = json.dumps(error_payload)
            return [mcp_types.TextContent(type="text", text=error_text)]
    else:
        logger.warning(f"MCP Server: Tool '{name}' not found/exposed by this server.")
        error_payload = {
            "success": False,
            "message": f"Tool '{name}' not implemented by this server.",
        }
        error_text = json.dumps(error_payload)
        return [mcp_types.TextContent(type="text", text=error_text)]


# --- MCP Server Runner ---
async def run_mcp_stdio_server():
    """Runs the MCP server, listening for connections over standard input/output.

    This function sets up a stdio-based transport for the MCP server and
    starts the main application loop to handle client requests. It also handles
    server initialization and graceful shutdown.
    """
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP Stdio Server: Starting handshake with client...")
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=app.name,
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
        logger.info("MCP Stdio Server: Run loop finished or client disconnected.")


# --- Main Entry Point ---
if __name__ == "__main__":
    logger.info("Launching SQLite DB MCP Server via stdio...")
    try:
        asyncio.run(run_mcp_stdio_server())
    except KeyboardInterrupt:
        logger.info("\nMCP Server (stdio) stopped by user.")
    except Exception as e:
        logger.critical(
            f"MCP Server (stdio) encountered an unhandled error: {e}", exc_info=True
        )
    finally:
        logger.info("MCP Server (stdio) process exiting.")
