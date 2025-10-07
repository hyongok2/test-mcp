"""
MCP (Model Context Protocol) HTTP Server for AI Agent Evaluation
A flexible MCP server implementation with web UI for tool management
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import uuid
import traceback

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn


# MCP Protocol Models
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


# Tool Registry System
class ToolRegistry:
    """Registry for managing MCP tools dynamically"""

    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._handlers: Dict[str, Callable] = {}
        self._call_history: List[Dict[str, Any]] = []

    def register_tool(self, tool: MCPTool, handler: Callable):
        """Register a new tool with its handler"""
        self._tools[tool.name] = tool
        self._handlers[tool.name] = handler

    def unregister_tool(self, tool_name: str):
        """Remove a tool from registry"""
        self._tools.pop(tool_name, None)
        self._handlers.pop(tool_name, None)

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get tool definition by name"""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[MCPTool]:
        """Get all registered tools"""
        return list(self._tools.values())

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool and record the call"""
        if tool_name not in self._handlers:
            raise ValueError(f"Tool '{tool_name}' not found")

        handler = self._handlers[tool_name]

        # Record call
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "arguments": arguments,
            "status": "pending"
        }

        try:
            # Execute handler (support both sync and async)
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)

            call_record["status"] = "success"
            call_record["result"] = result
            return result

        except Exception as e:
            call_record["status"] = "error"
            call_record["error"] = str(e)
            raise

        finally:
            self._call_history.append(call_record)
            # Keep only last 100 calls
            if len(self._call_history) > 100:
                self._call_history = self._call_history[-100:]

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get tool call history"""
        return self._call_history


# Initialize FastAPI app and tool registry
app = FastAPI(title="MCP Evaluation Server")
tool_registry = ToolRegistry()


# Sample evaluation tools
def register_sample_tools():
    """Register sample tools for evaluation"""

    # 1. Echo Tool
    echo_tool = MCPTool(
        name="echo",
        description="Echo back the input message",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo"
                }
            },
            "required": ["message"]
        }
    )

    def echo_handler(message: str) -> str:
        return f"Echo: {message}"

    tool_registry.register_tool(echo_tool, echo_handler)

    # 2. Calculator Tool
    calc_tool = MCPTool(
        name="calculate",
        description="Perform basic mathematical calculations",
        inputSchema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    )

    def calc_handler(expression: str) -> float:
        # Simple safe eval for basic math
        allowed_chars = "0123456789+-*/.()"
        if all(c in allowed_chars for c in expression.replace(" ", "")):
            return eval(expression)
        else:
            raise ValueError("Invalid mathematical expression")

    tool_registry.register_tool(calc_tool, calc_handler)

    # 3. Data Fetch Tool
    fetch_tool = MCPTool(
        name="fetch_data",
        description="Fetch mock data for testing",
        inputSchema={
            "type": "object",
            "properties": {
                "data_type": {
                    "type": "string",
                    "enum": ["user", "product", "order"],
                    "description": "Type of data to fetch"
                },
                "id": {
                    "type": "string",
                    "description": "ID of the resource"
                }
            },
            "required": ["data_type"]
        }
    )

    def fetch_handler(data_type: str, id: str = None) -> Dict[str, Any]:
        mock_data = {
            "user": {"id": id or "123", "name": "Test User", "email": "test@example.com"},
            "product": {"id": id or "456", "name": "Test Product", "price": 99.99},
            "order": {"id": id or "789", "status": "pending", "total": 199.99}
        }
        return mock_data.get(data_type, {})

    tool_registry.register_tool(fetch_tool, fetch_handler)

    # 4. Random Generator Tool
    random_tool = MCPTool(
        name="random",
        description="Generate random values",
        inputSchema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["number", "uuid", "boolean"],
                    "description": "Type of random value"
                },
                "min": {
                    "type": "number",
                    "description": "Minimum value (for number type)"
                },
                "max": {
                    "type": "number",
                    "description": "Maximum value (for number type)"
                }
            },
            "required": ["type"]
        }
    )

    import random

    def random_handler(type: str, min: float = 0, max: float = 100) -> Any:
        if type == "number":
            return random.uniform(min, max)
        elif type == "uuid":
            return str(uuid.uuid4())
        elif type == "boolean":
            return random.choice([True, False])
        else:
            return None

    tool_registry.register_tool(random_tool, random_handler)

    # 5. Delay Tool (for testing async operations)
    delay_tool = MCPTool(
        name="delay",
        description="Delay execution for testing",
        inputSchema={
            "type": "object",
            "properties": {
                "seconds": {
                    "type": "number",
                    "description": "Number of seconds to delay",
                    "minimum": 0,
                    "maximum": 10
                }
            },
            "required": ["seconds"]
        }
    )

    async def delay_handler(seconds: float) -> str:
        await asyncio.sleep(seconds)
        return f"Delayed for {seconds} seconds"

    tool_registry.register_tool(delay_tool, delay_handler)


# MCP Protocol Handlers
async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle initialize request"""
    return {
        "protocolVersion": "0.1.0",
        "serverInfo": {
            "name": "MCP Evaluation Server",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {},
            "prompts": {},
            "resources": {}
        }
    }


async def handle_list_tools(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request"""
    tools = tool_registry.get_all_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }
            for tool in tools
        ]
    }


async def handle_call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        result = await tool_registry.execute_tool(tool_name, arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result) if not isinstance(result, str) else result
                }
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# MCP Endpoint
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Main MCP protocol endpoint"""
    try:
        data = await request.json()
        mcp_request = MCPRequest(**data)

        # Route to appropriate handler
        handlers = {
            "initialize": handle_initialize,
            "tools/list": handle_list_tools,
            "tools/call": handle_call_tool,
        }

        handler = handlers.get(mcp_request.method)
        if not handler:
            return MCPResponse(
                id=mcp_request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {mcp_request.method}"
                }
            )

        result = await handler(mcp_request.params or {})

        return MCPResponse(
            id=mcp_request.id,
            result=result
        )

    except Exception as e:
        return MCPResponse(
            id=data.get("id") if "data" in locals() else None,
            error={
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        )


# Web UI Endpoints
@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Serve the web UI"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCP Evaluation Server</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            header {
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }

            h1 {
                color: #333;
                margin-bottom: 10px;
            }

            .subtitle {
                color: #666;
                font-size: 16px;
            }

            .main-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
            }

            .card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }

            .card h2 {
                color: #333;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #f0f0f0;
            }

            .tools-grid {
                display: grid;
                gap: 15px;
            }

            .tool-card {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #667eea;
                transition: transform 0.2s, box-shadow 0.2s;
            }

            .tool-card:hover {
                transform: translateX(5px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
            }

            .tool-name {
                font-weight: 600;
                color: #667eea;
                font-size: 18px;
                margin-bottom: 5px;
            }

            .tool-description {
                color: #666;
                font-size: 14px;
                margin-bottom: 10px;
            }

            .tool-schema {
                background: white;
                padding: 10px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                max-height: 150px;
                overflow-y: auto;
            }

            .history-item {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                font-size: 14px;
            }

            .history-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
            }

            .history-tool {
                font-weight: 600;
                color: #667eea;
            }

            .history-time {
                color: #999;
                font-size: 12px;
            }

            .history-status {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }

            .status-success {
                background: #d4edda;
                color: #155724;
            }

            .status-error {
                background: #f8d7da;
                color: #721c24;
            }

            .status-pending {
                background: #fff3cd;
                color: #856404;
            }

            .test-section {
                grid-column: 1 / -1;
            }

            .test-form {
                display: grid;
                grid-template-columns: 200px 1fr auto;
                gap: 15px;
                margin-top: 20px;
            }

            select, textarea, button {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-family: inherit;
            }

            select {
                background: white;
            }

            textarea {
                resize: vertical;
                min-height: 60px;
                font-family: 'Courier New', monospace;
            }

            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 30px;
                cursor: pointer;
                font-weight: 600;
                transition: background 0.2s;
            }

            button:hover {
                background: #5a67d8;
            }

            .result-box {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
                max-height: 300px;
                overflow-y: auto;
            }

            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }

            .stat-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }

            .stat-value {
                font-size: 24px;
                font-weight: 600;
                color: #667eea;
            }

            .stat-label {
                color: #666;
                font-size: 14px;
                margin-top: 5px;
            }

            @media (max-width: 768px) {
                .main-grid {
                    grid-template-columns: 1fr;
                }

                .test-form {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🤖 MCP Evaluation Server</h1>
                <div class="subtitle">Model Context Protocol HTTP Server for AI Agent Testing</div>
            </header>

            <div class="main-grid">
                <div class="card">
                    <h2>📦 Available Tools</h2>
                    <div class="tools-grid" id="toolsList">
                        <!-- Tools will be loaded here -->
                    </div>
                </div>

                <div class="card">
                    <h2>📊 Statistics</h2>
                    <div class="stats" id="stats">
                        <div class="stat-card">
                            <div class="stat-value" id="totalTools">0</div>
                            <div class="stat-label">Total Tools</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="totalCalls">0</div>
                            <div class="stat-label">Total Calls</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="successRate">0%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                    </div>

                    <h2 style="margin-top: 30px;">📜 Recent Activity</h2>
                    <div id="historyList">
                        <!-- History will be loaded here -->
                    </div>
                </div>

                <div class="card test-section">
                    <h2>🧪 Test Tool</h2>
                    <div class="test-form">
                        <select id="toolSelect">
                            <option value="">Select a tool...</option>
                        </select>
                        <textarea id="argumentsInput" placeholder='{"key": "value"}'></textarea>
                        <button onclick="testTool()">Execute</button>
                    </div>
                    <div id="testResult"></div>
                </div>
            </div>
        </div>

        <script>
            let tools = [];

            async function loadTools() {
                try {
                    const response = await fetch('/api/tools');
                    tools = await response.json();

                    const toolsList = document.getElementById('toolsList');
                    const toolSelect = document.getElementById('toolSelect');

                    toolsList.innerHTML = tools.map(tool => `
                        <div class="tool-card">
                            <div class="tool-name">${tool.name}</div>
                            <div class="tool-description">${tool.description}</div>
                            <div class="tool-schema">
                                <pre>${JSON.stringify(tool.inputSchema, null, 2)}</pre>
                            </div>
                        </div>
                    `).join('');

                    toolSelect.innerHTML = '<option value="">Select a tool...</option>' +
                        tools.map(tool => `<option value="${tool.name}">${tool.name}</option>`).join('');

                    document.getElementById('totalTools').textContent = tools.length;
                } catch (error) {
                    console.error('Failed to load tools:', error);
                }
            }

            async function loadHistory() {
                try {
                    const response = await fetch('/api/history');
                    const history = await response.json();

                    const historyList = document.getElementById('historyList');

                    if (history.length === 0) {
                        historyList.innerHTML = '<div style="color: #999; text-align: center; padding: 20px;">No activity yet</div>';
                    } else {
                        historyList.innerHTML = history.slice(-5).reverse().map(item => `
                            <div class="history-item">
                                <div class="history-header">
                                    <span class="history-tool">${item.tool}</span>
                                    <span class="history-time">${new Date(item.timestamp).toLocaleTimeString()}</span>
                                </div>
                                <div>
                                    <span class="history-status status-${item.status}">${item.status.toUpperCase()}</span>
                                </div>
                            </div>
                        `).join('');
                    }

                    // Update statistics
                    document.getElementById('totalCalls').textContent = history.length;

                    if (history.length > 0) {
                        const successCount = history.filter(h => h.status === 'success').length;
                        const successRate = Math.round((successCount / history.length) * 100);
                        document.getElementById('successRate').textContent = successRate + '%';
                    }
                } catch (error) {
                    console.error('Failed to load history:', error);
                }
            }

            async function testTool() {
                const toolName = document.getElementById('toolSelect').value;
                const argumentsInput = document.getElementById('argumentsInput').value;

                if (!toolName) {
                    alert('Please select a tool');
                    return;
                }

                let arguments;
                try {
                    arguments = JSON.parse(argumentsInput || '{}');
                } catch (error) {
                    alert('Invalid JSON in arguments');
                    return;
                }

                const resultBox = document.getElementById('testResult');
                resultBox.innerHTML = '<div class="result-box">Executing...</div>';

                try {
                    const response = await fetch('/mcp', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            jsonrpc: '2.0',
                            method: 'tools/call',
                            params: {
                                name: toolName,
                                arguments: arguments
                            },
                            id: Date.now()
                        })
                    });

                    const result = await response.json();

                    if (result.error) {
                        resultBox.innerHTML = `<div class="result-box" style="border-left: 4px solid #dc3545;">Error: ${result.error.message}</div>`;
                    } else {
                        resultBox.innerHTML = `<div class="result-box" style="border-left: 4px solid #28a745;">${JSON.stringify(result.result, null, 2)}</div>`;
                    }

                    // Reload history to show new call
                    loadHistory();
                } catch (error) {
                    resultBox.innerHTML = `<div class="result-box" style="border-left: 4px solid #dc3545;">Error: ${error.message}</div>`;
                }
            }

            // Load initial data
            loadTools();
            loadHistory();

            // Auto-refresh history every 5 seconds
            setInterval(loadHistory, 5000);

            // Set sample arguments when tool is selected
            document.getElementById('toolSelect').addEventListener('change', function() {
                const selectedTool = tools.find(t => t.name === this.value);
                if (selectedTool) {
                    const sampleArgs = {};
                    const props = selectedTool.inputSchema.properties || {};

                    for (const [key, schema] of Object.entries(props)) {
                        if (schema.type === 'string') {
                            sampleArgs[key] = schema.enum ? schema.enum[0] : 'sample';
                        } else if (schema.type === 'number') {
                            sampleArgs[key] = schema.minimum || 1;
                        } else if (schema.type === 'boolean') {
                            sampleArgs[key] = true;
                        }
                    }

                    document.getElementById('argumentsInput').value = JSON.stringify(sampleArgs, null, 2);
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content


# API Endpoints for Web UI
@app.get("/api/tools")
async def get_tools():
    """Get all registered tools"""
    return tool_registry.get_all_tools()


@app.get("/api/history")
async def get_history():
    """Get tool call history"""
    return tool_registry.get_call_history()


@app.post("/api/tools")
async def add_tool(tool_data: Dict[str, Any]):
    """Add a new tool dynamically"""
    try:
        tool = MCPTool(**tool_data["definition"])

        # Create a dynamic handler based on the provided code
        # Note: In production, this should be sandboxed for security
        handler_code = tool_data.get("handler", "")

        # Simple handler compilation (for demo purposes)
        exec_globals = {}
        exec(handler_code, exec_globals)
        handler = exec_globals.get("handler")

        if not handler:
            raise ValueError("Handler function not found in provided code")

        tool_registry.register_tool(tool, handler)
        return {"status": "success", "message": f"Tool '{tool.name}' registered"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/tools/{tool_name}")
async def remove_tool(tool_name: str):
    """Remove a tool from registry"""
    tool_registry.unregister_tool(tool_name)
    return {"status": "success", "message": f"Tool '{tool_name}' removed"}


# Main entry point
if __name__ == "__main__":
    # Register sample tools on startup
    register_sample_tools()

    print("🚀 MCP Evaluation Server starting...")
    print("📍 Server URL: http://localhost:8000")
    print("🔧 MCP Endpoint: http://localhost:8000/mcp")
    print("🌐 Web UI: http://localhost:8000")
    print("\nPress Ctrl+C to stop the server")

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)