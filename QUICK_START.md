# 🚀 삼성SDI EMS MCP 서버 - 빠른 시작

## ✅ Docker 이미지 빌드 완료!

Docker 이미지가 성공적으로 빌드되었습니다:
- **이미지 이름**: `samsung-sdi-ems-server:latest`
- **이미지 크기**: 487MB
- **Python 버전**: 3.11

## 🔥 즉시 실행 방법

### 1. Docker 단독 실행 (권장)
```bash
# 포트 8888에서 실행
docker run -d -p 8888:8000 --name samsung-sdi-ems samsung-sdi-ems-server:latest

# 또는 포트 9000에서 실행
docker run -d -p 9000:8000 --name samsung-sdi-ems samsung-sdi-ems-server:latest
```

### 2. Docker Compose 실행
```bash
# 프로덕션 모드
docker-compose up -d

# 개발 모드 (코드 변경 시 자동 반영)
docker-compose -f docker-compose.dev.yml up -d
```

### 3. 편리한 빌드 스크립트
```bash
# Windows
build.bat

# Linux/Mac
chmod +x build.sh && ./build.sh
```

## 🌐 접속 정보

### Docker 단독 실행 시
- **웹 UI**: http://localhost:8888
- **MCP 엔드포인트**: http://localhost:8888/mcp
- **헬스체크**: http://localhost:8888/health

### Docker Compose 실행 시
- **웹 UI**: http://localhost:8000
- **MCP 엔드포인트**: http://localhost:8000/mcp
- **헬스체크**: http://localhost:8000/health

## 📊 헬스체크 확인

```bash
# Docker 단독 실행 시
curl http://localhost:8888/health

# Docker Compose 실행 시
curl http://localhost:8000/health
```

**정상 응답 예시**:
```json
{
  "server": "Samsung SDI EMS MCP Server",
  "status": "healthy",
  "timestamp": "2025-10-02T06:59:14.353962",
  "tools_count": 5,
  "total_calls": 0,
  "version": "1.0.0"
}
```

## 🔧 삼성SDI EMS 도구들

1. **equipment_status_query** - 설비 실시간 상태 및 가동률 조회
2. **production_report** - 배터리 셀 생산 실적 리포트 생성
3. **maintenance_history** - 설비 정비 및 알람 이력 조회
4. **quality_analysis** - 배터리 셀 품질 데이터 분석 및 불량 통계
5. **energy_monitoring** - 공정별 에너지 사용량 모니터링 및 분석

## 🧪 도구 테스트 예시

웹 UI에서 다음과 같이 테스트할 수 있습니다:

### 설비 상태 조회
```json
{
  "equipment_id": "MIXER-001",
  "metric_type": "all"
}
```

### 생산 실적 리포트
```json
{
  "date_from": "2025-01-01",
  "date_to": "2025-01-07",
  "product_type": "21700",
  "report_format": "summary"
}
```

### 설비 이력 조회
```json
{
  "equipment_id": "COATER-002",
  "history_type": "maintenance",
  "days": 30
}
```

## 🐳 Docker 관리 명령어

```bash
# 컨테이너 상태 확인
docker ps

# 로그 확인
docker logs -f samsung-sdi-ems

# 컨테이너 중지
docker stop samsung-sdi-ems

# 컨테이너 재시작
docker restart samsung-sdi-ems

# 컨테이너 삭제
docker rm -f samsung-sdi-ems

# 이미지 재빌드
docker build -t samsung-sdi-ems-server:latest .
```

## 🚨 트러블슈팅

### 포트 충돌 시
```bash
# 다른 포트 사용
docker run -d -p 9999:8000 --name samsung-sdi-ems samsung-sdi-ems-server:latest
```

### 컨테이너 이름 충돌 시
```bash
# 기존 컨테이너 제거 후 재실행
docker rm -f samsung-sdi-ems
docker run -d -p 8888:8000 --name samsung-sdi-ems samsung-sdi-ems-server:latest
```

### CORS 오류 시
```bash
# 환경 변수로 허용 도메인 설정
docker run -d -p 8888:8000 -e CORS_ORIGINS="https://your-domain.com" --name samsung-sdi-ems samsung-sdi-ems-server:latest
```

## 🎯 AI Agent 연동

MCP 프로토콜로 다음과 같이 연동할 수 있습니다:

```python
import requests

# MCP 서버와 통신
def call_mcp_tool(tool_name, arguments):
    response = requests.post(
        "http://localhost:8888/mcp",  # Docker 단독 실행 시
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

# 설비 상태 조회 예시
result = call_mcp_tool("equipment_status_query", {
    "equipment_id": "MIXER-001",
    "metric_type": "all"
})
print(result)
```

## 🎉 성공!

Docker 이미지가 성공적으로 빌드되고 실행되었습니다. 이제 AI Agent가 삼성SDI 이차전지 제조 현장과 유사한 환경에서 EMS 데이터를 다루는 능력을 평가할 수 있습니다!