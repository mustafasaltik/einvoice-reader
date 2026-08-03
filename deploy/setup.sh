#!/usr/bin/env bash
# Run as root on the server after cloning the repo.
# Usage: bash /home/einvoice/einvoice-reader/deploy/setup.sh
set -e

APP_DIR=/home/einvoice/einvoice-reader

echo "==> Installing systemd service"
cp "$APP_DIR/deploy/einvoice-reader.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable einvoice-reader
systemctl restart einvoice-reader
systemctl status einvoice-reader --no-pager

echo "==> Configuring nginx"
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/einvoice-reader
ln -sf /etc/nginx/sites-available/einvoice-reader /etc/nginx/sites-enabled/einvoice-reader
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> Obtaining SSL certificate"
certbot --nginx -d einvoice-reader.com -d www.einvoice-reader.com --non-interactive --agree-tos --email mustafasaltikk@gmail.com --redirect

echo "==> Done. Site is live at https://einvoice-reader.com"
