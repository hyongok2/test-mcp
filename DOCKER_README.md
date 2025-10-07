# 🐳 Samsung SDI EMS MCP Server - Docker 배포 가이드

## 빠른 시작

### 1. 단독 Docker 실행
```bash
# 이미지 빌드
docker build -t samsung-sdi-ems-server .

# 컨테이너 실행
docker run -p 8000:8000 samsung-sdi-ems-server
```

### 2. Docker Compose 실행 (권장)
```bash
# 프로덕션 모드
docker-compose up -d

# 개발 모드 (코드 변경 시 자동 반영)
docker-compose -f docker-compose.dev.yml up -d
```

### 3. 편리한 빌드 스크립트
```bash
# Linux/Mac
chmod +x build.sh
./build.sh

# Windows
build.bat
```

## 접속 정보

- **웹 UI**: http://localhost:8000
- **MCP 엔드포인트**: http://localhost:8000/mcp
- **헬스체크**: http://localhost:8000/health

## 환경 변수 설정

### 기본 환경 변수
```bash
FLASK_ENV=production              # 환경 모드
CORS_ORIGINS=*                   # 허용할 도메인 (개발용)
PYTHONUNBUFFERED=1              # Python 로그 실시간 출력
```

### 프로덕션 환경 변수
```bash
# docker-compose.yml 수정 또는 .env 파일 생성
FLASK_ENV=production
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com
```

## 프로덕션 배포

### 1. AWS/GCP/Azure 클라우드
```bash
# 이미지 빌드 및 푸시
docker build -t your-registry/samsung-sdi-ems-server .
docker push your-registry/samsung-sdi-ems-server

# 클라우드에서 실행
docker run -d \
  -p 8000:8000 \
  -e FLASK_ENV=production \
  -e CORS_ORIGINS=https://your-domain.com \
  --name mcp-server \
  your-registry/samsung-sdi-ems-server
```

### 2. Docker Swarm 배포
```yaml
# docker-stack.yml
version: '3.8'
services:
  mcp-server:
    image: samsung-sdi-ems-server:latest
    ports:
      - "8000:8000"
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

```bash
docker stack deploy -c docker-stack.yml mcp-stack
```

### 3. Kubernetes 배포
```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: samsung-sdi-ems-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: samsung-sdi-ems-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: CORS_ORIGINS
          value: "https://your-domain.com"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server-service
spec:
  selector:
    app: mcp-server
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

## 모니터링

### 헬스체크 확인
```bash
curl http://localhost:8000/health
```

### 로그 확인
```bash
# Docker Compose
docker-compose logs -f mcp-server

# Docker 단독
docker logs -f samsung-sdi-ems-server
```

### 컨테이너 상태 확인
```bash
docker ps
docker stats samsung-sdi-ems-server
```

## 트러블슈팅

### 포트 충돌
```bash
# 다른 포트 사용
docker run -p 9000:8000 samsung-sdi-ems-server
```

### 메모리 부족
```bash
# 메모리 제한 설정
docker run -m 512m -p 8000:8000 samsung-sdi-ems-server
```

### CORS 오류
```bash
# 환경 변수로 허용 도메인 설정
docker run -e CORS_ORIGINS="https://your-domain.com" -p 8000:8000 samsung-sdi-ems-server
```

## 성능 최적화

### 1. 멀티 스테이지 빌드 (고급)
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "mcp_server_flask.py"]
```

### 2. 리소스 제한
```yaml
# docker-compose.yml에 추가
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## 보안 설정

### 1. 비-루트 사용자로 실행
```dockerfile
# Dockerfile에 추가
RUN useradd -m -u 1000 appuser
USER appuser
```

### 2. 시크릿 관리
```bash
# Docker Secrets 사용
echo "your-secret-key" | docker secret create api_key -
```

## 백업 및 복구

### 데이터 볼륨 백업
```bash
# 백업
docker run --rm -v mcp_data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# 복구
docker run --rm -v mcp_data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /
```

## 자주 사용하는 명령어

```bash
# 전체 스택 시작
docker-compose up -d

# 서비스 재시작
docker-compose restart mcp-server

# 로그 실시간 확인
docker-compose logs -f

# 컨테이너 내부 접근
docker-compose exec mcp-server bash

# 전체 스택 중지 및 정리
docker-compose down -v

# 이미지 재빌드
docker-compose build --no-cache
```