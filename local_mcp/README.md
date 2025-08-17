# Local MCP Server for ADK Agent

In this application, the ADK web agent uses the `MCPToolset` to communicate with custom local MCP server (server.py) via a **stdio-based handshake**.

## Here’s how the process works in this context

### 1. Agent Setup (`agent.py`)

- The ADK agent is configured with a toolset (`MCPToolset`) that knows how to launch MCP server using the Python command and the path to server.py.
- The agent’s toolset uses `StdioConnectionParams`, meaning it will communicate with the MCP server over standard input/output (not over a network socket).

### 2. MCP Server Launch

- When ADK web starts, it launches MCP server as a subprocess using the command specified in `agent.py`.
- The MCP server (server.py) starts up, initializes logging, and waits for a handshake from the client (the ADK agent).

### 3. Handshake and Tool Discovery

- The ADK agent sends an initialization message to the MCP server.
- The MCP server responds, advertising its available tools (like `list_db_tables`, `get_table_schema`, etc.) and their input schemas.
- This handshake ensures both sides know what functions are available and how to call them.

### 4. Tool Invocation

- When the ADK agent needs to perform a database operation, it sends a request (e.g., `CallToolRequest`) to the MCP server via stdio.
- The MCP server receives the request, executes the corresponding database utility function, and returns the result.

### 5. Result Handling

- The ADK agent receives the result and uses it to fulfill the user’s request in the web interface.

---

**Summary:**  
The ADK web agent uses `MCPToolset` to launch and handshake with custom MCP server over stdio. The server advertises its tools, receives requests, executes database operations, and returns results—all through a structured stdio protocol. This enables seamless integration of custom database logic with the ADK agent’s capabilities.
