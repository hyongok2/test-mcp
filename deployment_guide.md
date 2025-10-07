# MCP Server 배포 가이드

## CORS 설정

### 개발 환경 (현재 설정)
```python
CORS_ORIGINS = ["*"]  # 모든 도메인 허용
```

### 프로덕션 환경 설정 방법

#### 1. config.py 수정
```python
class ProductionConfig(Config):
    CORS_ORIGINS = [
        "https://your-frontend.com",
        "https://your-ai-agent.com",
        "https://app.yourdomain.com"
    ]
```

#### 2. 환경 변수 설정
```bash
export FLASK_ENV=production
export CORS_ORIGINS="https://domain1.com,https://domain2.com"
```

## 서버 배포 옵션

### 1. 클라우드 서버 (AWS/GCP/Azure)

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt

# 프로덕션 서버 실행 (Gunicorn 사용)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 mcp_server_flask:app
```

### 2. Docker 배포

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV CORS_ORIGINS="https://your-domain.com"

EXPOSE 8000

CMD ["python", "mcp_server_flask.py"]
```

### 3. Nginx 리버스 프록시 설정

```nginx
server {
    listen 80;
    server_name your-mcp-server.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS Headers (if needed)
        add_header 'Access-Control-Allow-Origin' 'https://your-frontend.com' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
    }

    location /mcp {
        proxy_pass http://localhost:8000/mcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # MCP specific settings
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

## 보안 고려사항

### 1. HTTPS 설정 (필수)
```bash
# Let's Encrypt 사용
sudo certbot --nginx -d your-mcp-server.com
```

### 2. API 인증 추가
```python
# API Key 인증 예시
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/mcp", methods=["POST"])
@require_api_key
def mcp_endpoint():
    # ... existing code
```

### 3. Rate Limiting 추가
```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter

limiter = Limiter(
    app=app,
    key_func=lambda: request.remote_addr,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/mcp", methods=["POST"])
@limiter.limit("10 per minute")
def mcp_endpoint():
    # ... existing code
```

### 4. 입력 검증 강화
```python
# Tool handler 실행 시 샌드박싱
import ast
import RestrictedPython

def safe_exec_handler(code, arguments):
    # RestrictedPython으로 안전한 실행 환경 구성
    restricted_globals = {...}
    exec(compile_restricted(code), restricted_globals)
    return restricted_globals['handler'](**arguments)
```

## 모니터링

### 로깅 설정
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)
```

### 헬스체크 엔드포인트
```python
@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tools_count": len(tool_registry.get_all_tools())
    })
```

## 프로덕션 체크리스트

- [ ] FLASK_ENV를 'production'으로 설정
- [ ] DEBUG 모드 비활성화
- [ ] CORS origins를 특정 도메인으로 제한
- [ ] HTTPS 설정
- [ ] API 인증 구현
- [ ] Rate limiting 설정
- [ ] 로깅 및 모니터링 구성
- [ ] 백업 전략 수립
- [ ] 에러 처리 강화
- [ ] 입력 검증 및 샌드박싱

## 환경별 실행 방법

### 개발
```bash
export FLASK_ENV=development
python mcp_server_flask.py
```

### 프로덕션
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:8000 mcp_server_flask:app
```

### Docker
```bash
docker build -t mcp-server .
docker run -p 8000:8000 -e CORS_ORIGINS="https://your-domain.com" mcp-server
```