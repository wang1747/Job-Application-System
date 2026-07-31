# 后端 Dockerfile
FROM python:3.13-slim

WORKDIR /app

# 安装系统依赖（PyPDF2 需要）
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/
COPY run.py .

# 设置 Python 路径
ENV PYTHONPATH=/app/backend

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["python", "run.py"]
