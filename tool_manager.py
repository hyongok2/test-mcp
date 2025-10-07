"""
Dynamic Tool Manager for MCP Server
Allows adding, modifying, and removing tools at runtime
"""

import json
from typing import Dict, Any, Callable
from mcp_server import MCPTool, tool_registry


class DynamicToolManager:
    """Manager for dynamically creating and managing MCP tools"""

    @staticmethod
    def create_string_tool(name: str, description: str) -> MCPTool:
        """Create a simple string processing tool"""
        return MCPTool(
            name=name,
            description=description,
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input string to process"
                    }
                },
                "required": ["input"]
            }
        )

    @staticmethod
    def create_data_tool(name: str, description: str, properties: Dict[str, Any]) -> MCPTool:
        """Create a data processing tool with custom schema"""
        return MCPTool(
            name=name,
            description=description,
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": list(properties.keys())
            }
        )

    @staticmethod
    def create_query_tool(name: str, description: str, query_types: list) -> MCPTool:
        """Create a query-based tool"""
        return MCPTool(
            name=name,
            description=description,
            inputSchema={
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": query_types,
                        "description": "Type of query to execute"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Query parameters"
                    }
                },
                "required": ["query_type"]
            }
        )


# Example custom tools to add
def register_custom_evaluation_tools():
    """Register additional evaluation-specific tools"""

    # 1. Performance Benchmark Tool
    perf_tool = MCPTool(
        name="benchmark",
        description="Measure performance metrics",
        inputSchema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["cpu", "memory", "io"],
                    "description": "Type of benchmark"
                },
                "duration": {
                    "type": "number",
                    "description": "Duration in seconds",
                    "minimum": 0.1,
                    "maximum": 10
                }
            },
            "required": ["operation"]
        }
    )

    import time
    import psutil

    def benchmark_handler(operation: str, duration: float = 1.0) -> Dict[str, Any]:
        start_time = time.time()

        if operation == "cpu":
            cpu_percent = psutil.cpu_percent(interval=duration)
            return {
                "metric": "cpu_usage",
                "value": cpu_percent,
                "unit": "percent",
                "duration": duration
            }
        elif operation == "memory":
            mem = psutil.virtual_memory()
            return {
                "metric": "memory_usage",
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent,
                "unit": "bytes"
            }
        elif operation == "io":
            io_stats = psutil.disk_io_counters()
            time.sleep(duration)
            io_stats_after = psutil.disk_io_counters()
            return {
                "metric": "io_stats",
                "read_bytes": io_stats_after.read_bytes - io_stats.read_bytes,
                "write_bytes": io_stats_after.write_bytes - io_stats.write_bytes,
                "duration": duration
            }

        return {"error": "Unknown operation"}

    tool_registry.register_tool(perf_tool, benchmark_handler)

    # 2. Validation Tool
    validation_tool = MCPTool(
        name="validate",
        description="Validate data against rules",
        inputSchema={
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Data to validate"
                },
                "rules": {
                    "type": "object",
                    "description": "Validation rules",
                    "properties": {
                        "required_fields": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "field_types": {
                            "type": "object"
                        }
                    }
                }
            },
            "required": ["data", "rules"]
        }
    )

    def validate_handler(data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        errors = []

        # Check required fields
        required_fields = rules.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check field types
        field_types = rules.get("field_types", {})
        for field, expected_type in field_types.items():
            if field in data:
                actual_type = type(data[field]).__name__
                if actual_type != expected_type:
                    errors.append(f"Field '{field}' should be {expected_type}, got {actual_type}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": data
        }

    tool_registry.register_tool(validation_tool, validate_handler)

    # 3. Mock API Tool
    api_tool = MCPTool(
        name="mock_api",
        description="Simulate API calls for testing",
        inputSchema={
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                    "description": "HTTP method"
                },
                "endpoint": {
                    "type": "string",
                    "description": "API endpoint path"
                },
                "data": {
                    "type": "object",
                    "description": "Request data (for POST/PUT)"
                }
            },
            "required": ["method", "endpoint"]
        }
    )

    def api_handler(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        # Simulate different API responses
        mock_responses = {
            "/users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "/products": [
                {"id": 1, "name": "Widget", "price": 19.99},
                {"id": 2, "name": "Gadget", "price": 29.99}
            ],
            "/status": {
                "status": "healthy",
                "version": "1.0.0"
            }
        }

        if method == "GET":
            response = mock_responses.get(endpoint, {"error": "Not found"})
        elif method == "POST":
            response = {"id": 3, "created": True, "data": data}
        elif method == "PUT":
            response = {"updated": True, "data": data}
        elif method == "DELETE":
            response = {"deleted": True, "endpoint": endpoint}
        else:
            response = {"error": "Method not supported"}

        return {
            "method": method,
            "endpoint": endpoint,
            "response": response,
            "status_code": 200 if "error" not in str(response) else 404
        }

    tool_registry.register_tool(api_tool, api_handler)

    # 4. State Management Tool
    state_tool = MCPTool(
        name="state",
        description="Manage application state for testing",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "set", "clear", "list"],
                    "description": "State action"
                },
                "key": {
                    "type": "string",
                    "description": "State key"
                },
                "value": {
                    "description": "Value to set (for set action)"
                }
            },
            "required": ["action"]
        }
    )

    # Simple in-memory state storage
    state_storage = {}

    def state_handler(action: str, key: str = None, value: Any = None) -> Dict[str, Any]:
        if action == "get":
            if key:
                return {"key": key, "value": state_storage.get(key)}
            return {"error": "Key required for get action"}

        elif action == "set":
            if key:
                state_storage[key] = value
                return {"key": key, "value": value, "action": "set"}
            return {"error": "Key required for set action"}

        elif action == "clear":
            if key:
                if key in state_storage:
                    del state_storage[key]
                    return {"key": key, "action": "cleared"}
                return {"error": f"Key '{key}' not found"}
            else:
                state_storage.clear()
                return {"action": "all_cleared"}

        elif action == "list":
            return {"keys": list(state_storage.keys()), "count": len(state_storage)}

        return {"error": "Unknown action"}

    tool_registry.register_tool(state_tool, state_handler)


if __name__ == "__main__":
    # Example of how to use the tool manager
    manager = DynamicToolManager()

    # Create a simple string tool
    uppercase_tool = manager.create_string_tool(
        name="uppercase",
        description="Convert string to uppercase"
    )

    # Create the handler
    def uppercase_handler(input: str) -> str:
        return input.upper()

    # Register it
    tool_registry.register_tool(uppercase_tool, uppercase_handler)

    print("Custom tools registered successfully!")