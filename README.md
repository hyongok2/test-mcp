# MCP Evaluation Server

AI Agent 평가를 위한 MCP (Model Context Protocol) HTTP 서버 구현

## 특징

- **HTTP 기반 MCP 프로토콜**: `/mcp` 엔드포인트를 통한 표준 MCP 통신
- **웹 UI**: 실시간으로 도구 확인 및 테스트 가능
- **동적 도구 관리**: 런타임에 도구 추가/수정/삭제 가능
- **평가 도구 내장**: 테스트용 다양한 도구 제공
- **실시간 모니터링**: 호출 기록 및 통계 확인

## 설치

```bash
pip install -r requirements.txt
```

추가 기능을 위해 psutil 설치 (선택사항):
```bash
pip install psutil
```

## 실행

```bash
python mcp_server.py
```

서버가 시작되면:
- MCP Endpoint: `http://localhost:8000/mcp`
- Web UI: `http://localhost:8000`

## 내장 도구

### 1. echo
입력 메시지를 그대로 반환

### 2. calculate
기본적인 수학 계산 수행

### 3. fetch_data
테스트용 모의 데이터 반환 (user, product, order)

### 4. random
랜덤 값 생성 (number, uuid, boolean)

### 5. delay
비동기 작업 테스트를 위한 지연 실행

## 추가 평가 도구 (tool_manager.py)

### 6. benchmark
성능 메트릭 측정 (CPU, Memory, I/O)

### 7. validate
데이터 유효성 검증

### 8. mock_api
API 호출 시뮬레이션

### 9. state
상태 관리 테스트

## MCP 프로토콜 사용

### Initialize
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {},
  "id": 1
}
```

### List Tools
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 2
}
```

### Call Tool
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {
      "message": "Hello, MCP!"
    }
  },
  "id": 3
}
```

## 동적 도구 추가

### API를 통한 도구 추가

```python
import requests

tool_definition = {
    "definition": {
        "name": "my_tool",
        "description": "My custom tool",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            },
            "required": ["param"]
        }
    },
    "handler": """
def handler(param):
    return f"Processed: {param}"
"""
}

response = requests.post("http://localhost:8000/api/tools", json=tool_definition)
```

### 코드로 도구 추가

```python
from mcp_server import MCPTool, tool_registry

# 도구 정의
my_tool = MCPTool(
    name="my_custom_tool",
    description="Custom tool for testing",
    inputSchema={
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    }
)

# 핸들러 함수
def my_handler(input: str):
    return f"Custom result: {input}"

# 등록
tool_registry.register_tool(my_tool, my_handler)
```

## AI Agent 연동

이 서버는 HTTP 기반 MCP 프로토콜을 지원하는 모든 AI Agent와 연동 가능합니다.

### 연동 예시

```python
import requests

# MCP 서버와 통신
def call_mcp_tool(tool_name, arguments):
    response = requests.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
    )
    return response.json()

# 도구 호출
result = call_mcp_tool("calculate", {"expression": "2 + 2"})
print(result)
```

## 확장 가능성

- 새로운 도구를 tool_manager.py에 추가
- 웹 UI를 통한 실시간 도구 관리
- API를 통한 동적 도구 추가/삭제
- 평가 메트릭 수집 및 분석 기능 확장 가능