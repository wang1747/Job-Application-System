.PHONY: help install run test docker-build docker-up docker-down clean

help:
	@echo "可用命令:"
	@echo "  make install      - 安装依赖"
	@echo "  make run          - 启动开发服务"
	@echo "  make test         - 运行测试"
	@echo "  make docker-build - 构建 Docker 镜像"
	@echo "  make docker-up    - 启动 Docker 容器"
	@echo "  make docker-down  - 停止 Docker 容器"
	@echo "  make clean        - 清理缓存"

install:
	uv sync

run:
	uv run python run.py

test:
	PYTHONPATH=backend uv run python -m pytest backend/tests/ -v

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache