#!/bin/bash

# Docker 이미지 빌드 스크립트
echo "🐳 Samsung SDI EMS MCP Server Docker 이미지 빌드 중..."

# 이미지 빌드
docker build -t samsung-sdi-ems-server:latest .

# 빌드 성공 확인
if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 완료!"
    echo "📋 빌드된 이미지:"
    docker images | grep samsung-sdi-ems-server
else
    echo "❌ Docker 이미지 빌드 실패!"
    exit 1
fi

echo ""
echo "🚀 실행 방법:"
echo "1. 단독 실행: docker run -p 8000:8000 samsung-sdi-ems-server:latest"
echo "2. Docker Compose: docker-compose up -d"
echo "3. 개발 모드: docker-compose -f docker-compose.dev.yml up"