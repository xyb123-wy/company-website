#!/bin/bash
# 苏州清韵项目管理系统 - VPS 一键部署脚本 (Ubuntu/Debian)
# 使用方法: curl -sSL https://raw.githubusercontent.com/xyb123-wy/company-website/master/deploy.sh | bash
# 或: git clone 后 bash deploy.sh

set -e

APP_DIR="/opt/company-website"
APP_USER="www-data"
DOMAIN="${1:-}"

echo "===== 苏州清韵项目管理系统 - 部署开始 ====="

# 1. 安装系统依赖
echo "[1/6] 安装系统依赖..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nginx git

# 2. 克隆代码
echo "[2/6] 克隆代码..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull origin master
else
    git clone https://github.com/xyb123-wy/company-website.git "$APP_DIR"
    cd "$APP_DIR"
fi

# 3. 创建虚拟环境并安装依赖
echo "[3/6] 安装 Python 依赖..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
deactivate

# 4. 初始化数据库
echo "[4/6] 初始化数据库..."
cd "$APP_DIR"
source venv/bin/activate
python3 init_db.py
deactivate

# 5. 创建 systemd 服务
echo "[5/6] 配置 systemd 服务..."
cat > /etc/systemd/system/company-website.service << SYSTEMD
[Unit]
Description=苏州清韵项目管理系统
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn app:app -b 127.0.0.1:8000 --workers=2 --timeout=120
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SYSTEMD

systemctl daemon-reload
systemctl enable company-website
systemctl restart company-website

# 6. 配置 Nginx
echo "[6/6] 配置 Nginx 反向代理..."

if [ -n "$DOMAIN" ]; then
    SERVER_NAME="$DOMAIN"
else
    SERVER_NAME="_"
fi

cat > /etc/nginx/sites-available/company-website << NGINX
server {
    listen 80;
    server_name $SERVER_NAME;
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $APP_DIR/;
    }

    location /uploads/ {
        alias $APP_DIR/uploads/;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/company-website /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# 设置权限
chown -R $APP_USER:$APP_USER "$APP_DIR"
chmod -R 755 "$APP_DIR"

echo "===== 部署完成! ====="
echo ""
echo "网站已启动，通过以下方式访问："
echo "  http://$(curl -s ifconfig.me)"
if [ -n "$DOMAIN" ]; then
    echo "  http://$DOMAIN"
fi
echo ""
echo "后台管理地址："
echo "  http://YOUR_IP/admin"
echo "  账号: admin / admin123"
echo ""
echo "管理命令："
echo "  systemctl status company-website   # 查看状态"
echo "  systemctl restart company-website  # 重启"
echo "  journalctl -u company-website -f   # 查看日志"
