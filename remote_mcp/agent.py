import json
import os

from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

from .prompt import NOTION_PROMPT

# ---- Load Environment Variables ----
load_dotenv()

MODEL_NAME: str | None = os.getenv(key="GEMINI_MODEL", default="gemini-2.0-flash")
if MODEL_NAME is None:
    raise ValueError("GEMINI_MODEL is not set")

# ---- MCP Library ----
# https://github.com/modelcontextprotocol/servers
# https://smithery.ai/

# ---- Notion -----
# https://developers.notion.com/docs/mcp
# https://github.com/makenotion/notion-mcp-server
# https://github.com/makenotion/notion-mcp-server/blob/main/scripts/notion-openapi.json

NOTION_API_KEY: str | None = os.getenv(key="NOTION_API_KEY")
if NOTION_API_KEY is None:
    raise ValueError("NOTION_API_KEY is not set")

# ---- Notion MCP Headers ----
NOTION_MCP_HEADERS = json.dumps(
    {"Authorization": f"Bearer {NOTION_API_KEY}", "Notion-Version": "2022-06-28"}
)

# ----Root Agent ----
root_agent = Agent(
    model=MODEL_NAME,
    name="Notion_MCP_Agent",
    instruction=NOTION_PROMPT,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=["-y", "@notionhq/notion-mcp-server"],
                env={"OPENAPI_MCP_HEADERS": NOTION_MCP_HEADERS},
            )
        ),
    ],
)
