# server.py
import sys
from pathlib import Path

# Setting absolute path for imports to work when ADK Agent runs the server.py directly
sys.path.insert(0, str((Path(__file__).parent / "..").resolve()))

import asyncio
import json
import logging  # Added logging

import mcp.server.stdio  # For running as a stdio server
from dotenv import load_dotenv

# ADK Tool Imports
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

# MCP Server Imports
from mcp import types as mcp_types  # Use alias to avoid conflict
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Local Database Utility Imports
from local_mcp.db_utils import (
    delete_data,
    get_table_schema,
    insert_data,
    list_db_tables,
    query_db_table,
)

# --- Load Environment Variables ---
load_dotenv()

# --- Logging Setup ---
LOG_FILE_PATH = str((Path(__file__).parent / "mcp_server_activity.log").resolve())
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, mode="w"),
    ],
)

# --- MCP Server Setup ---
logging.info(
    "Creating MCP Server instance for SQLite DB..."
)  # Changed print to logging.info
app = Server("sqlite-db-mcp-server")

# Wrap database utility functions as ADK FunctionTools
ADK_DB_TOOLS = {
    "list_db_tables": FunctionTool(func=list_db_tables),
    "get_table_schema": FunctionTool(func=get_table_schema),
    "query_db_table": FunctionTool(func=query_db_table),
    "insert_data": FunctionTool(func=insert_data),
    "delete_data": FunctionTool(func=delete_data),
}


@app.list_tools()
async def list_mcp_tools() -> list[mcp_types.Tool]:
    """MCP handler to list tools this server exposes."""
    logging.info(
        "MCP Server: Received list_tools request."
    )  # Changed print to logging.info
    mcp_tools_list = []
    for tool_name, adk_tool_instance in ADK_DB_TOOLS.items():
        if not adk_tool_instance.name:
            adk_tool_instance.name = tool_name

        mcp_tool_schema = adk_to_mcp_tool_type(adk_tool_instance)
        logging.info(  # Changed print to logging.info
            f"MCP Server: Advertising tool: {mcp_tool_schema.name}, InputSchema: {mcp_tool_schema.inputSchema}"
        )
        mcp_tools_list.append(mcp_tool_schema)
    return mcp_tools_list


@app.call_tool()
async def call_mcp_tool(name: str, arguments: dict) -> list[mcp_types.TextContent]:
    """MCP handler to execute a tool call requested by an MCP client."""
    logging.info(
        f"MCP Server: Received call_tool request for '{name}' with args: {arguments}"
    )  # Changed print to logging.info

    if name in ADK_DB_TOOLS:
        adk_tool_instance = ADK_DB_TOOLS[name]
        try:
            adk_tool_response = await adk_tool_instance.run_async(
                args=arguments,
                tool_context=None,  # type: ignore
            )
            logging.info(  # Changed print to logging.info
                f"MCP Server: ADK tool '{name}' executed. Response: {adk_tool_response}"
            )
            response_text = json.dumps(adk_tool_response, indent=2)
            return [mcp_types.TextContent(type="text", text=response_text)]

        except Exception as e:
            logging.error(
                f"MCP Server: Error executing ADK tool '{name}': {e}", exc_info=True
            )  # Changed print to logging.error, added exc_info
            error_payload = {
                "success": False,
                "message": f"Failed to execute tool '{name}': {str(e)}",
            }
            error_text = json.dumps(error_payload)
            return [mcp_types.TextContent(type="text", text=error_text)]
    else:
        logging.warning(
            f"MCP Server: Tool '{name}' not found/exposed by this server."
        )  # Changed print to logging.warning
        error_payload = {
            "success": False,
            "message": f"Tool '{name}' not implemented by this server.",
        }
        error_text = json.dumps(error_payload)
        return [mcp_types.TextContent(type="text", text=error_text)]


# --- MCP Server Runner ---
async def run_mcp_stdio_server():
    """Runs the MCP server, listening for connections over standard input/output."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logging.info(
            "MCP Stdio Server: Starting handshake with client..."
        )  # Changed print to logging.info
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
        logging.info(
            "MCP Stdio Server: Run loop finished or client disconnected."
        )  # Changed print to logging.info


# --- Main Entry Point ---
if __name__ == "__main__":
    logging.info(
        "Launching SQLite DB MCP Server via stdio..."
    )  # Changed print to logging.info
    try:
        asyncio.run(run_mcp_stdio_server())
    except KeyboardInterrupt:
        logging.info(
            "\nMCP Server (stdio) stopped by user."
        )  # Changed print to logging.info
    except Exception as e:
        logging.critical(
            f"MCP Server (stdio) encountered an unhandled error: {e}", exc_info=True
        )  # Changed print to logging.critical, added exc_info
    finally:
        logging.info(
            "MCP Server (stdio) process exiting."
        )  # Changed print to logging.info
