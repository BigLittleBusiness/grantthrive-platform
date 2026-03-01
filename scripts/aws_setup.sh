#!/usr/bin/env bash
# =============================================================================
# GrantThrive Backend — AWS EC2 Server Setup Script
# =============================================================================
# Run this script ONCE on a fresh Ubuntu 22.04 EC2 instance to prepare it
# for automated CI/CD deployments from GitHub Actions.
#
# Usage:
#   chmod +x aws_setup.sh
#   sudo ./aws_setup.sh
#
# What this script does:
#   1. Installs Python 3.11, pip, venv, and system dependencies
#   2. Installs and configures Nginx
#   3. Creates the /srv/grantthrive directory structure
#   4. Installs the grantthrive-backend systemd service
#   5. Creates a deploy user with passwordless sudo for systemctl restart
#   6. Adds the GitHub Actions SSH public key to authorized_keys
# =============================================================================

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Must run as root ──────────────────────────────────────────────────────────
[[ $EUID -eq 0 ]] || error "This script must be run as root (sudo ./aws_setup.sh)"

info "Starting GrantThrive backend server setup..."

# ── 1. System packages ────────────────────────────────────────────────────────
info "Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python3.11 python3.11-venv python3-pip \
    nginx certbot python3-certbot-nginx \
    git curl rsync \
    build-essential libpq-dev \
    postgresql-client

# ── 2. Directory structure ────────────────────────────────────────────────────
info "Creating /srv/grantthrive directory structure..."
mkdir -p /srv/grantthrive/releases
mkdir -p /srv/grantthrive/shared/logs
mkdir -p /srv/grantthrive/shared/uploads
mkdir -p /srv/grantthrive/shared/reports_output
chown -R ubuntu:ubuntu /srv/grantthrive

# ── 3. Systemd service ────────────────────────────────────────────────────────
info "Installing grantthrive-backend systemd service..."
cat > /etc/systemd/system/grantthrive-backend.service << 'SERVICE'
[Unit]
Description=GrantThrive Backend (Gunicorn + Flask)
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/srv/grantthrive/current
EnvironmentFile=/srv/grantthrive/current/.env
ExecStart=/srv/grantthrive/current/venv/bin/gunicorn \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /srv/grantthrive/shared/logs/access.log \
    --error-logfile  /srv/grantthrive/shared/logs/error.log \
    wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable grantthrive-backend
info "Systemd service installed and enabled."

# ── 4. Sudoers rule for GitHub Actions deploy user ────────────────────────────
info "Adding passwordless sudo rule for systemctl restart..."
cat > /etc/sudoers.d/grantthrive-deploy << 'SUDOERS'
# Allow the ubuntu user to restart/reload GrantThrive services without a password
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart grantthrive-backend
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl is-active grantthrive-backend
SUDOERS
chmod 440 /etc/sudoers.d/grantthrive-deploy
info "Sudoers rule added."

# ── 5. Nginx configuration ────────────────────────────────────────────────────
info "Writing Nginx configuration..."
cat > /etc/nginx/sites-available/grantthrive << 'NGINX'
# GrantThrive — Nginx configuration
# Serves the frontend static files and reverse-proxies API calls to Gunicorn.
# Run: sudo certbot --nginx -d grantthrive.com -d app.grantthrive.com ...
# to add SSL after this file is in place.

server {
    listen 80;
    server_name grantthrive.com www.grantthrive.com app.grantthrive.com
                admin.grantthrive.com map.grantthrive.com roi.grantthrive.com;

    # Frontend static files
    root /var/www/grantthrive/current;
    index index.html;

    # SPA fallback — all non-asset requests serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API — proxy to Gunicorn
    location /api/ {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Security headers
    add_header X-Frame-Options        "SAMEORIGIN"   always;
    add_header X-Content-Type-Options "nosniff"      always;
    add_header Referrer-Policy        "strict-origin" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/javascript application/json
               application/x-javascript text/xml application/xml image/svg+xml;
    gzip_min_length 1000;
}
NGINX

ln -sf /etc/nginx/sites-available/grantthrive /etc/nginx/sites-enabled/grantthrive
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
info "Nginx configured and reloaded."

# ── 6. Frontend directory ─────────────────────────────────────────────────────
info "Creating frontend directory structure..."
mkdir -p /var/www/grantthrive/releases
chown -R ubuntu:ubuntu /var/www/grantthrive

echo ""
info "=========================================================="
info "  Server setup complete!"
info "=========================================================="
echo ""
warn "Next steps:"
warn "  1. Add the GitHub Actions SSH public key to /home/ubuntu/.ssh/authorized_keys"
warn "     (see the CI/CD setup guide for instructions)"
warn "  2. Run: sudo certbot --nginx -d grantthrive.com -d app.grantthrive.com \\"
warn "           -d admin.grantthrive.com -d map.grantthrive.com -d roi.grantthrive.com"
warn "  3. Add all required GitHub Secrets to both repositories"
warn "     (see docs/cicd-setup-guide.md)"
echo ""
