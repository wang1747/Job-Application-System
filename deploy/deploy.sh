#!/usr/bin/env bash
# ============================================================
#  OfferFlow 一键部署脚本（生产环境）
#  服务器上执行：bash deploy/deploy.sh
#  前提：已装 Docker + docker compose 插件
# ============================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "  OfferFlow 生产部署"
echo "=========================================="

# ---------- 1. 检查 Docker ----------
if ! command -v docker &>/dev/null; then
    echo "[ERROR] 未安装 Docker，请先安装："
    echo "  curl -fsSL https://get.docker.com | sh"
    echo "  systemctl enable --now docker"
    exit 1
fi

if ! docker compose version &>/dev/null; then
    echo "[ERROR] 未安装 docker compose 插件"
    exit 1
fi

echo "[OK] Docker 已安装"

# ---------- 2. 生成 .env.prod（首次）----------
ENV_FILE="$PROJECT_ROOT/.env.prod"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "[2/6] 首次部署，生成 .env.prod ..."
    cp "$PROJECT_ROOT/.env.prod.example" "$ENV_FILE"

    # 自动生成密钥
    PG_PASS=$(openssl rand -base64 24 2>/dev/null || head -c 32 /dev/urandom | base64)
    JWT_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p -c 64)
    ENC_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p -c 64)
    DEF_PASS=$(openssl rand -hex 8 2>/dev/null || head -c 8 /dev/urandom | xxd -p -c 16)
    REM_TOKEN=$(openssl rand -hex 16 2>/dev/null || head -c 16 /dev/urandom | xxd -p -c 32)

    sed -i "s|POSTGRES_PASSWORD=???|POSTGRES_PASSWORD=${PG_PASS}|" "$ENV_FILE"
    sed -i "s|DEFAULT_USER_PASSWORD=???|DEFAULT_USER_PASSWORD=${DEF_PASS}|" "$ENV_FILE"
    sed -i "s|JWT_SECRET_KEY=???|JWT_SECRET_KEY=${JWT_KEY}|" "$ENV_FILE"
    sed -i "s|ENCRYPTION_KEY=???|ENCRYPTION_KEY=${ENC_KEY}|" "$ENV_FILE"
    sed -i "s|REMINDER_SERVICE_TOKEN=???|REMINDER_SERVICE_TOKEN=${REM_TOKEN}|" "$ENV_FILE"

    echo "  -> .env.prod 已生成，密钥已自动填充"
    echo ""
    echo "  ============================================"
    echo "  请手动编辑以下项后再继续："
    echo "  "
    echo "  1. DEEPSEEK_API_KEY    填你的 DeepSeek API Key"
    echo "  2. CORS_ORIGINS        改成你的真实域名 https://xxx"
    echo "  3. DEFAULT_USER_NAME / PASSWORD  改掉默认管理员"
    echo "  ============================================"
    echo ""
    echo "  默认管理员临时密码: ${DEF_PASS}"
    echo "  （请记录后立即在 App 内修改）"
    echo ""
    read -rp "编辑完 .env.prod 后按回车继续，或 Ctrl+C 退出..."
else
    echo "[2/6] .env.prod 已存在，跳过"
fi

# ---------- 3. 证书检查 ----------
CERT_DIR="$PROJECT_ROOT/deploy/certs"
if [ ! -f "$CERT_DIR/cert.pem" ] || [ ! -f "$CERT_DIR/key.pem" ]; then
    echo ""
    echo "[3/6] 未找到 SSL 证书，生成自签证书（仅测试用）..."
    mkdir -p "$CERT_DIR"
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" \
        -days 365 -subj "/CN=offferflow" 2>/dev/null
    echo "  -> 自签证书已生成（生产请替换为 Let's Encrypt）"
    echo "     申请免费证书：https://certbot.eff.org/"
else
    echo "[3/6] SSL 证书已就绪"
fi

# ---------- 4. 构建 + 启动 ----------
echo ""
echo "[4/6] 构建镜像..."
docker compose -f docker-compose.prod.yml --env-file .env.prod build

echo ""
echo "[5/6] 启动服务..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# ---------- 5. 等待健康检查 ----------
echo ""
echo "[6/6] 等待服务就绪..."
for i in $(seq 1 30); do
    if curl -sf http://localhost/health &>/dev/null || curl -sf http://localhost/api/health &>/dev/null; then
        echo "  -> 服务已就绪!"
        break
    fi
    echo "  等待中... ($i/30)"
    sleep 2
done

# ---------- 6. 完成 ----------
echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo ""
echo "  前端:   http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost')"
echo "  API:    http://localhost/api/health"
echo ""
echo "  常用命令:"
echo "    查看日志:  docker compose -f docker-compose.prod.yml logs -f"
echo "    重启:      docker compose -f docker-compose.prod.yml restart"
echo "    停止:      docker compose -f docker-compose.prod.yml down"
echo "    更新:      git pull && docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "  数据库备份位置: ./backups (每日自动 pg_dump)"
echo ""
