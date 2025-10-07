"""
MCP (Model Context Protocol) HTTP Server for AI Agent Evaluation - Flask Version
A flexible MCP server implementation with web UI for tool management
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import uuid
import traceback
import random
import time
from dataclasses import dataclass, asdict

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS


# MCP Protocol Models using dataclasses
@dataclass
class MCPTool:
    name: str
    description: str
    inputSchema: Dict[str, Any]


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

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
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
            # Execute handler
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


# Initialize Flask app and tool registry
app = Flask(__name__)

# CORS configuration for production
# For development: Allow all origins
# For production: Replace '*' with your specific domain(s)
CORS(app,
     resources={
         r"/mcp": {
             "origins": "*",  # Change to specific domains in production: ["https://yourdomain.com"]
             "methods": ["POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": False,
             "max_age": 3600
         },
         r"/api/*": {
             "origins": "*",  # Change to specific domains in production
             "methods": ["GET", "POST", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type"],
             "supports_credentials": False
         }
     }
)

tool_registry = ToolRegistry()


# Sample evaluation tools - Samsung SDI EMS (Equipment Management System)
def register_sample_tools():
    """삼성SDI EMS 평가용 도구들 등록"""

    # 1. 설비 상태 조회 도구
    equipment_status_tool = MCPTool(
        name="equipment_status_query",
        description="설비 실시간 상태 및 가동률 조회",
        inputSchema={
            "type": "object",
            "properties": {
                "equipment_id": {
                    "type": "string",
                    "description": "설비 ID (예: MIXER-001, COATER-002)"
                },
                "metric_type": {
                    "type": "string",
                    "enum": ["status", "oee", "temperature", "pressure", "all"],
                    "description": "조회할 메트릭 유형"
                }
            },
            "required": ["equipment_id"]
        }
    )

    def equipment_status_handler(equipment_id: str, metric_type: str = "all") -> Dict[str, Any]:
        # 실제 DB 쿼리 시뮬레이션
        base_data = {
            "equipment_id": equipment_id,
            "equipment_name": f"혼합기 {equipment_id[-3:]}" if "MIXER" in equipment_id else f"코팅기 {equipment_id[-3:]}",
            "location": "천안공장 2동",
            "query_time": datetime.now().isoformat()
        }

        if metric_type in ["status", "all"]:
            base_data["status"] = random.choice(["운전중", "정지", "점검중", "알람"])
            base_data["running_time"] = f"{random.randint(1, 24)}시간 {random.randint(0, 59)}분"

        if metric_type in ["oee", "all"]:
            base_data["oee"] = {
                "availability": round(random.uniform(85, 99), 2),
                "performance": round(random.uniform(80, 95), 2),
                "quality": round(random.uniform(95, 99.9), 2),
                "overall": round(random.uniform(75, 92), 2)
            }

        if metric_type in ["temperature", "all"]:
            base_data["temperature"] = {
                "current": round(random.uniform(20, 80), 1),
                "setpoint": 65.0,
                "unit": "°C",
                "alarm_high": 85.0,
                "alarm_low": 15.0
            }

        if metric_type in ["pressure", "all"]:
            base_data["pressure"] = {
                "current": round(random.uniform(0.8, 1.2), 3),
                "setpoint": 1.0,
                "unit": "MPa"
            }

        return base_data

    tool_registry.register_tool(equipment_status_tool, equipment_status_handler)

    # 2. 생산 실적 리포트 생성 도구
    production_report_tool = MCPTool(
        name="production_report",
        description="배터리 셀 생산 실적 리포트 생성",
        inputSchema={
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "조회 시작일 (YYYY-MM-DD)"
                },
                "date_to": {
                    "type": "string",
                    "description": "조회 종료일 (YYYY-MM-DD)"
                },
                "product_type": {
                    "type": "string",
                    "enum": ["21700", "18650", "46800", "pouch", "all"],
                    "description": "배터리 셀 타입"
                },
                "report_format": {
                    "type": "string",
                    "enum": ["summary", "detailed", "daily"],
                    "description": "리포트 형식"
                }
            },
            "required": ["date_from", "date_to"]
        }
    )

    def production_report_handler(date_from: str, date_to: str, product_type: str = "all", report_format: str = "summary") -> Dict[str, Any]:
        # 생산 실적 데이터 생성
        report = {
            "report_id": f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "period": f"{date_from} ~ {date_to}",
            "product_type": product_type,
            "report_type": report_format,
            "generation_time": datetime.now().isoformat()
        }

        if report_format == "summary":
            report["summary"] = {
                "total_production": random.randint(50000, 200000),
                "good_quantity": random.randint(48000, 195000),
                "defect_quantity": random.randint(100, 5000),
                "yield_rate": round(random.uniform(95, 99.5), 2),
                "capacity_utilization": round(random.uniform(75, 95), 2)
            }

        if report_format in ["detailed", "daily"]:
            report["production_lines"] = [
                {
                    "line_id": f"LINE-{i:02d}",
                    "production": random.randint(10000, 30000),
                    "yield_rate": round(random.uniform(94, 99), 2),
                    "downtime_minutes": random.randint(0, 120),
                    "main_product": random.choice(["21700", "18650", "46800"])
                }
                for i in range(1, 6)
            ]

        if report_format == "daily":
            report["daily_trend"] = [
                {
                    "date": (datetime.strptime(date_from, "%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "production": random.randint(8000, 15000),
                    "yield_rate": round(random.uniform(95, 99), 2)
                }
                for i in range(7)
            ]

        report["sql_query"] = f"SELECT * FROM production_records WHERE date BETWEEN '{date_from}' AND '{date_to}'"

        return report

    tool_registry.register_tool(production_report_tool, production_report_handler)

    # 3. 설비 이력 조회 도구
    maintenance_history_tool = MCPTool(
        name="maintenance_history",
        description="설비 정비 및 알람 이력 조회",
        inputSchema={
            "type": "object",
            "properties": {
                "equipment_id": {
                    "type": "string",
                    "description": "설비 ID"
                },
                "history_type": {
                    "type": "string",
                    "enum": ["maintenance", "alarm", "parameter_change", "all"],
                    "description": "이력 유형"
                },
                "days": {
                    "type": "number",
                    "description": "조회 기간 (일)",
                    "minimum": 1,
                    "maximum": 365
                }
            },
            "required": ["equipment_id"]
        }
    )

    def maintenance_history_handler(equipment_id: str, history_type: str = "all", days: int = 30) -> Dict[str, Any]:
        history = {
            "equipment_id": equipment_id,
            "query_period": f"최근 {days}일",
            "query_time": datetime.now().isoformat()
        }

        if history_type in ["maintenance", "all"]:
            history["maintenance_records"] = [
                {
                    "date": (datetime.now() - timedelta(days=random.randint(1, days))).strftime("%Y-%m-%d"),
                    "type": random.choice(["정기점검", "예방정비", "고장수리", "부품교체"]),
                    "description": random.choice([
                        "모터 베어링 교체",
                        "필터 청소 및 교체",
                        "센서 캘리브레이션",
                        "컨트롤러 펌웨어 업데이트"
                    ]),
                    "downtime_hours": round(random.uniform(0.5, 8), 1),
                    "technician": f"기술자-{random.randint(101, 120)}"
                }
                for _ in range(random.randint(2, 5))
            ]

        if history_type in ["alarm", "all"]:
            history["alarm_records"] = [
                {
                    "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24*days))).isoformat(),
                    "alarm_code": f"ALM-{random.randint(1000, 9999)}",
                    "severity": random.choice(["Critical", "Warning", "Info"]),
                    "description": random.choice([
                        "온도 상한 초과",
                        "압력 이상 감지",
                        "진동 수치 경고",
                        "전류 과부하"
                    ]),
                    "duration_minutes": random.randint(1, 60),
                    "action_taken": random.choice(["자동복구", "수동리셋", "정비조치"])
                }
                for _ in range(random.randint(3, 8))
            ]

        if history_type in ["parameter_change", "all"]:
            history["parameter_changes"] = [
                {
                    "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24*days))).isoformat(),
                    "parameter": random.choice(["온도설정값", "속도", "압력", "혼합비율"]),
                    "old_value": round(random.uniform(50, 70), 1),
                    "new_value": round(random.uniform(50, 70), 1),
                    "changed_by": f"엔지니어-{random.randint(201, 210)}",
                    "reason": "공정 최적화"
                }
                for _ in range(random.randint(1, 4))
            ]

        return history

    tool_registry.register_tool(maintenance_history_tool, maintenance_history_handler)

    # 4. 품질 데이터 분석 도구
    quality_analysis_tool = MCPTool(
        name="quality_analysis",
        description="배터리 셀 품질 데이터 분석 및 불량 통계",
        inputSchema={
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": ["defect_pareto", "trend", "correlation", "specification"],
                    "description": "분석 유형"
                },
                "product_type": {
                    "type": "string",
                    "description": "제품 타입 (예: 21700)"
                },
                "batch_id": {
                    "type": "string",
                    "description": "배치 ID (선택사항)"
                }
            },
            "required": ["analysis_type"]
        }
    )

    def quality_analysis_handler(analysis_type: str, product_type: str = "21700", batch_id: str = None) -> Dict[str, Any]:
        result = {
            "analysis_type": analysis_type,
            "product_type": product_type,
            "batch_id": batch_id or f"BATCH-{random.randint(10000, 99999)}",
            "analysis_time": datetime.now().isoformat()
        }

        if analysis_type == "defect_pareto":
            result["defect_analysis"] = {
                "total_inspected": random.randint(10000, 50000),
                "total_defects": random.randint(50, 500),
                "defect_rate_ppm": random.randint(100, 5000),
                "top_defects": [
                    {"type": "전압불량", "count": random.randint(10, 100), "percentage": round(random.uniform(20, 40), 1)},
                    {"type": "용량부족", "count": random.randint(5, 80), "percentage": round(random.uniform(15, 30), 1)},
                    {"type": "외관불량", "count": random.randint(5, 50), "percentage": round(random.uniform(10, 20), 1)},
                    {"type": "내부저항", "count": random.randint(2, 30), "percentage": round(random.uniform(5, 15), 1)},
                    {"type": "기타", "count": random.randint(1, 20), "percentage": round(random.uniform(1, 10), 1)}
                ]
            }

        elif analysis_type == "trend":
            result["trend_data"] = {
                "period": "최근 7일",
                "average_yield": round(random.uniform(96, 99), 2),
                "trend_direction": random.choice(["상승", "안정", "하락"]),
                "daily_yield": [
                    {
                        "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                        "yield_rate": round(random.uniform(95, 99.5), 2),
                        "production": random.randint(8000, 12000)
                    }
                    for i in range(7, 0, -1)
                ]
            }

        elif analysis_type == "specification":
            result["specification_check"] = {
                "voltage": {
                    "spec": "3.6V ± 0.05V",
                    "mean": round(random.uniform(3.58, 3.62), 3),
                    "std_dev": round(random.uniform(0.01, 0.03), 3),
                    "cpk": round(random.uniform(1.2, 2.0), 2)
                },
                "capacity": {
                    "spec": "4800mAh ± 50mAh",
                    "mean": round(random.uniform(4790, 4810), 1),
                    "std_dev": round(random.uniform(10, 30), 1),
                    "cpk": round(random.uniform(1.3, 1.8), 2)
                },
                "resistance": {
                    "spec": "< 20mΩ",
                    "mean": round(random.uniform(15, 19), 1),
                    "std_dev": round(random.uniform(1, 3), 1),
                    "cpk": round(random.uniform(1.1, 1.5), 2)
                }
            }

        return result

    tool_registry.register_tool(quality_analysis_tool, quality_analysis_handler)

    # 5. 에너지 사용량 모니터링 도구
    energy_monitoring_tool = MCPTool(
        name="energy_monitoring",
        description="공정별 에너지 사용량 모니터링 및 분석",
        inputSchema={
            "type": "object",
            "properties": {
                "monitoring_type": {
                    "type": "string",
                    "enum": ["realtime", "daily", "monthly", "comparison"],
                    "description": "모니터링 유형"
                },
                "process": {
                    "type": "string",
                    "enum": ["mixing", "coating", "drying", "assembly", "formation", "all"],
                    "description": "공정 구분"
                },
                "energy_type": {
                    "type": "string",
                    "enum": ["electricity", "gas", "steam", "all"],
                    "description": "에너지 유형"
                }
            },
            "required": ["monitoring_type"]
        }
    )

    def energy_monitoring_handler(monitoring_type: str, process: str = "all", energy_type: str = "all") -> Dict[str, Any]:
        result = {
            "monitoring_type": monitoring_type,
            "process": process,
            "energy_type": energy_type,
            "timestamp": datetime.now().isoformat()
        }

        if monitoring_type == "realtime":
            result["realtime_data"] = {
                "current_power_kw": round(random.uniform(500, 2000), 1),
                "today_consumption_kwh": round(random.uniform(5000, 15000), 1),
                "peak_power_kw": round(random.uniform(1800, 2500), 1),
                "power_factor": round(random.uniform(0.92, 0.98), 3),
                "cost_krw_per_hour": round(random.uniform(50000, 150000), 0)
            }

        elif monitoring_type == "daily":
            result["daily_summary"] = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_consumption_kwh": round(random.uniform(10000, 25000), 1),
                "peak_demand_kw": round(random.uniform(1500, 2500), 1),
                "average_load_kw": round(random.uniform(800, 1500), 1),
                "cost_krw": round(random.uniform(1000000, 3000000), 0),
                "co2_emissions_kg": round(random.uniform(4000, 10000), 1)
            }

        elif monitoring_type == "comparison":
            result["comparison_data"] = {
                "current_month": {
                    "consumption_kwh": round(random.uniform(300000, 500000), 0),
                    "cost_krw": round(random.uniform(30000000, 50000000), 0)
                },
                "previous_month": {
                    "consumption_kwh": round(random.uniform(280000, 480000), 0),
                    "cost_krw": round(random.uniform(28000000, 48000000), 0)
                },
                "change_percentage": round(random.uniform(-10, 10), 1),
                "efficiency_index": round(random.uniform(0.85, 0.95), 3)
            }

        if process != "all":
            result["process_breakdown"] = {
                "mixing": round(random.uniform(15, 25), 1),
                "coating": round(random.uniform(20, 30), 1),
                "drying": round(random.uniform(25, 35), 1),
                "assembly": round(random.uniform(10, 20), 1),
                "formation": round(random.uniform(15, 25), 1)
            }

        return result

    tool_registry.register_tool(energy_monitoring_tool, energy_monitoring_handler)


# MCP Protocol Handlers
def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
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


def handle_list_tools(params: Dict[str, Any]) -> Dict[str, Any]:
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


def handle_call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        result = tool_registry.execute_tool(tool_name, arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result) if not isinstance(result, str) else result
                }
            ]
        }
    except ValueError as e:
        raise Exception(str(e))
    except Exception as e:
        raise Exception(str(e))


# MCP Endpoint
@app.route("/mcp", methods=["POST", "OPTIONS"])
def mcp_endpoint():
    """Main MCP protocol endpoint"""
    # Handle preflight request
    if request.method == "OPTIONS":
        return "", 200

    try:
        data = request.json
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")

        # Debug logging
        print(f"[MCP] Request - method: {method}, id: {request_id}, params: {params}")

        # Route to appropriate handler
        handlers = {
            "initialize": handle_initialize,
            "tools/list": handle_list_tools,
            "tools/call": handle_call_tool,
        }

        handler = handlers.get(method)
        if not handler:
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            print(f"[MCP] Error: Method not found - {method}")
            return jsonify(error_response)

        result = handler(params)

        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

        print(f"[MCP] Success - id: {request_id}, result type: {type(result)}")
        return jsonify(response)

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[MCP] Exception: {error_trace}")

        error_response = {
            "jsonrpc": "2.0",
            "id": request_id if 'request_id' in locals() else None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }
        return jsonify(error_response)


# Web UI HTML template
HTML_TEMPLATE = """
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

        /* Tool Creator Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
        }

        .modal-content {
            position: relative;
            background: white;
            margin: 50px auto;
            padding: 30px;
            width: 90%;
            max-width: 800px;
            border-radius: 12px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .modal-close {
            font-size: 28px;
            cursor: pointer;
            color: #999;
        }

        .modal-close:hover {
            color: #333;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }

        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-family: inherit;
        }

        .form-group textarea.code {
            font-family: 'Courier New', monospace;
            min-height: 200px;
        }

        .add-tool-btn {
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .add-tool-btn:hover {
            background: #218838;
        }

        .delete-tool-btn {
            background: #dc3545;
            color: white;
            padding: 5px 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            float: right;
        }

        .delete-tool-btn:hover {
            background: #c82333;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 삼성SDI EMS 평가 서버</h1>
            <div class="subtitle">이차전지 설비관리시스템 AI Agent 평가용 MCP 서버</div>
        </header>

        <div class="main-grid">
            <div class="card">
                <h2>📦 사용 가능한 도구</h2>
                <button class="add-tool-btn" onclick="showAddToolModal()">+ 새 도구 추가</button>
                <div class="tools-grid" id="toolsList">
                    <!-- Tools will be loaded here -->
                </div>
            </div>

            <div class="card">
                <h2>📊 통계</h2>
                <div class="stats" id="stats">
                    <div class="stat-card">
                        <div class="stat-value" id="totalTools">0</div>
                        <div class="stat-label">등록된 도구</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="totalCalls">0</div>
                        <div class="stat-label">총 호출 수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="successRate">0%</div>
                        <div class="stat-label">성공률</div>
                    </div>
                </div>

                <h2 style="margin-top: 30px;">📜 최근 활동</h2>
                <div id="historyList">
                    <!-- History will be loaded here -->
                </div>
            </div>

            <div class="card test-section">
                <h2>🧪 도구 테스트</h2>
                <div class="test-form">
                    <select id="toolSelect">
                        <option value="">도구를 선택하세요...</option>
                    </select>
                    <textarea id="argumentsInput" placeholder='{"equipment_id": "MIXER-001"}'></textarea>
                    <button onclick="testTool()">실행</button>
                </div>
                <div id="testResult"></div>
            </div>
        </div>
    </div>

    <!-- Add Tool Modal -->
    <div id="addToolModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>새 도구 생성</h2>
                <span class="modal-close" onclick="hideAddToolModal()">&times;</span>
            </div>

            <div class="form-group">
                <label for="toolName">도구 이름</label>
                <input type="text" id="toolName" placeholder="예: custom_equipment_query">
            </div>

            <div class="form-group">
                <label for="toolDescription">설명</label>
                <input type="text" id="toolDescription" placeholder="이 도구는 무엇을 하나요?">
            </div>

            <div class="form-group">
                <label for="toolSchema">입력 스키마 (JSON)</label>
                <textarea id="toolSchema" class="code" placeholder='{
    "type": "object",
    "properties": {
        "equipment_id": {
            "type": "string",
            "description": "설비 ID"
        }
    },
    "required": ["equipment_id"]
}'></textarea>
            </div>

            <div class="form-group">
                <label for="toolHandler">핸들러 함수 (Python)</label>
                <textarea id="toolHandler" class="code" placeholder='def handler(equipment_id):
    # 여기에 도구 로직을 작성하세요
    return f"설비 {equipment_id} 조회 결과"

# 참고: 함수 이름은 반드시 "handler"여야 합니다'></textarea>
            </div>

            <button class="button" onclick="addNewTool()">도구 생성</button>
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
                        <button class="delete-tool-btn" onclick="deleteTool('${tool.name}')">삭제</button>
                        <div class="tool-name">${tool.name}</div>
                        <div class="tool-description">${tool.description}</div>
                        <div class="tool-schema">
                            <pre>${JSON.stringify(tool.inputSchema, null, 2)}</pre>
                        </div>
                    </div>
                `).join('');

                toolSelect.innerHTML = '<option value="">도구를 선택하세요...</option>' +
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
                    historyList.innerHTML = '<div style="color: #999; text-align: center; padding: 20px;">아직 활동이 없습니다</div>';
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
                alert('도구를 선택하세요');
                return;
            }

            let toolArguments;
            try {
                toolArguments = JSON.parse(argumentsInput || '{}');
            } catch (error) {
                alert('잘못된 JSON 형식입니다');
                return;
            }

            const resultBox = document.getElementById('testResult');
            resultBox.innerHTML = '<div class="result-box">실행 중...</div>';

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
                            arguments: toolArguments
                        },
                        id: Date.now()
                    })
                });

                const result = await response.json();

                if (result.error) {
                    resultBox.innerHTML = `<div class="result-box" style="border-left: 4px solid #dc3545;">에러: ${result.error.message}</div>`;
                } else {
                    resultBox.innerHTML = `<div class="result-box" style="border-left: 4px solid #28a745;">${JSON.stringify(result.result, null, 2)}</div>`;
                }

                // Reload history to show new call
                loadHistory();
            } catch (error) {
                console.error('Tool execution error:', error);
                resultBox.innerHTML = `<div class="result-box" style="border-left: 4px solid #dc3545;">에러: ${error.message}</div>`;
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

        // Modal functions
        function showAddToolModal() {
            document.getElementById('addToolModal').style.display = 'block';
            // Set default values
            document.getElementById('toolSchema').value = JSON.stringify({
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["input"]
            }, null, 4);

            document.getElementById('toolHandler').value = `def handler(input):
    # Your tool logic here
    return f"Result: {input}"`;
        }

        function hideAddToolModal() {
            document.getElementById('addToolModal').style.display = 'none';
        }

        async function addNewTool() {
            const name = document.getElementById('toolName').value;
            const description = document.getElementById('toolDescription').value;
            const schemaText = document.getElementById('toolSchema').value;
            const handlerCode = document.getElementById('toolHandler').value;

            if (!name || !description || !schemaText || !handlerCode) {
                alert('Please fill in all fields');
                return;
            }

            let schema;
            try {
                schema = JSON.parse(schemaText);
            } catch (e) {
                alert('Invalid JSON in Input Schema');
                return;
            }

            try {
                const response = await fetch('/api/tools', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        definition: {
                            name: name,
                            description: description,
                            inputSchema: schema
                        },
                        handler: handlerCode
                    })
                });

                const result = await response.json();

                if (result.status === 'success') {
                    alert('Tool created successfully!');
                    hideAddToolModal();
                    // Clear form
                    document.getElementById('toolName').value = '';
                    document.getElementById('toolDescription').value = '';
                    // Reload tools
                    loadTools();
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (error) {
                alert('Failed to create tool: ' + error.message);
            }
        }

        async function deleteTool(toolName) {
            if (!confirm(`Are you sure you want to delete the tool "${toolName}"?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/tools/${toolName}`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (result.status === 'success') {
                    alert('Tool deleted successfully!');
                    loadTools();
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (error) {
                alert('Failed to delete tool: ' + error.message);
            }
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('addToolModal');
            if (event.target == modal) {
                hideAddToolModal();
            }
        }
    </script>
</body>
</html>
"""


# Web UI Endpoints
@app.route("/")
def web_ui():
    """Serve the web UI"""
    return render_template_string(HTML_TEMPLATE)


# API Endpoints for Web UI
@app.route("/api/tools")
def get_tools():
    """Get all registered tools"""
    tools = tool_registry.get_all_tools()
    return jsonify([asdict(tool) for tool in tools])


@app.route("/api/history")
def get_history():
    """Get tool call history"""
    return jsonify(tool_registry.get_call_history())


@app.route("/api/tools", methods=["POST"])
def add_tool():
    """Add a new tool dynamically"""
    try:
        tool_data = request.json
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
        return jsonify({"status": "success", "message": f"Tool '{tool.name}' registered"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/tools/<tool_name>", methods=["DELETE"])
def remove_tool(tool_name: str):
    """Remove a tool from registry"""
    tool_registry.unregister_tool(tool_name)
    return jsonify({"status": "success", "message": f"Tool '{tool_name}' removed"})


@app.route("/health")
def health_check():
    """Health check endpoint for Docker and load balancers"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "Samsung SDI EMS MCP Server",
        "version": "1.0.0",
        "tools_count": len(tool_registry.get_all_tools()),
        "total_calls": len(tool_registry.get_call_history())
    })


# Main entry point
if __name__ == "__main__":
    # Register sample tools on startup
    register_sample_tools()

    print("MCP Evaluation Server (Flask) starting...")
    print("Server URL: http://localhost:8000")
    print("MCP Endpoint: http://localhost:8000/mcp")
    print("Web UI: http://localhost:8000")
    print("\nPress Ctrl+C to stop the server")

    # Run the server
    app.run(host="0.0.0.0", port=8000, debug=True)