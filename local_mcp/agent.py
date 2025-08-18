import os
from pathlib import Path

from dotenv import load_dotenv

# ADK Imports
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

# MCP Imports
from mcp import StdioServerParameters

# Local Imports
from local_mcp.prompt import DB_MCP_PROMPT

# ---- Load Environment Variables ----
load_dotenv()

MODEL_NAME: str = os.getenv(key="MODEL_NAME", default="")

# ---- Path to MCP Server Script ----
PATH_TO_MCP_SERVER: str = str((Path(__file__).parent / "server.py").resolve())

# ---- Root Agent ----
root_agent = Agent(
    model=MODEL_NAME,
    name="local_db_mcp_client_agent",
    instruction=DB_MCP_PROMPT,
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python",
                    args=[PATH_TO_MCP_SERVER],
                ),
                timeout=60.0,  # Optional: specify a timeout in seconds
            )
        ),
    ],
)
