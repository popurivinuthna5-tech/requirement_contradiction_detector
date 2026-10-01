#!/bin/bash
# ==============================================================================
# AWS EC2 Automated Deployment Script for Requirement Conflict Analyzer
# Supports Ubuntu 22.04 / 24.04 LTS and Amazon Linux 2023
# ==============================================================================

set -e

echo "=========================================================="
echo "Starting Requirement Conflict & Overlap Analyzer Setup on EC2"
echo "=========================================================="

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

# 1. Detect OS and install system packages
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS=$(uname -s)
fi

echo "[1/6] Installing system dependencies for OS: $OS..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv nginx curl git build-essential
elif [ "$OS" = "amzn" ] || [ "$OS" = "fedora" ] || [ "$OS" = "rhel" ]; then
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip nginx curl git gcc
fi

# 2. Setup Python Virtual Environment
echo "[2/6] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Python Dependencies
echo "[3/6] Installing application dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Generate sample documents for immediate testing
echo "[4/6] Generating sample demo documents (PDF, DOCX, TXT)..."
python sample_data/generate_sample_docs.py || true

# 5. Setup Configuration
if [ ! -f .env ]; then
    echo "[5/6] Creating .env from template..."
    cp .env.example .env
fi

# 6. Configure Systemd Service
echo "[6/6] Configuring and starting systemd service..."
CURRENT_USER=$(whoami)
SERVICE_FILE="/etc/systemd/system/requirement-analyzer.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Requirement Conflict & Overlap Analyzer
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/run_server.py
Restart=always
RestartSec=5s
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin"
Environment="PORT=8000"
Environment="HOST=127.0.0.1"
Environment="ENVIRONMENT=production"

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable requirement-analyzer
sudo systemctl restart requirement-analyzer

# 7. Configure Nginx Reverse Proxy
echo "Configuring Nginx Reverse Proxy on port 80..."
if [ -d /etc/nginx/sites-available ]; then
    sudo cp deployment/nginx.conf /etc/nginx/sites-available/requirement-analyzer
    sudo ln -sf /etc/nginx/sites-available/requirement-analyzer /etc/nginx/sites-enabled/default
else
    sudo cp deployment/nginx.conf /etc/nginx/conf.d/requirement-analyzer.conf
fi

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# 8. Print Success Banner
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || curl -s https://ifconfig.me || echo "your-ec2-ip")

echo "=========================================================="
echo "DEPLOYMENT COMPLETE!"
echo "Requirement Conflict & Overlap Analyzer is now running."
echo ""
echo "Access the application via your browser at:"
echo "http://$PUBLIC_IP"
echo ""
echo "Check service logs anytime with:"
echo "sudo journalctl -u requirement-analyzer -f"
echo "=========================================================="
