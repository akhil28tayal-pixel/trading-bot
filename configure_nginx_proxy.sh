#!/bin/bash
# Configure Nginx Proxy for Dashboard
# Manual setup guide and configuration files

echo "Configuring Nginx Proxy for Dashboard"
echo "===================================="
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

cd /home/trader/trading_bot

echo "1. Creating nginx configuration for dashboard..."
cat > /tmp/dashboard_nginx.conf << 'NGINXCONF'
server {
    listen 80;
    server_name dashboard.atcpa.co;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    location / {
        proxy_pass http://127.0.0.1:5003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "Dashboard is healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINXCONF

echo "2. Creating SSL configuration (for future HTTPS)..."
cat > /tmp/dashboard_nginx_ssl.conf << 'NGINXSSL'
server {
    listen 80;
    server_name dashboard.atcpa.co;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dashboard.atcpa.co;

    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/dashboard.atcpa.co/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.atcpa.co/privkey.pem;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    location / {
        proxy_pass http://127.0.0.1:5003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINXSSL

echo "3. Creating supervisor configuration for dashboard..."
cat > /tmp/dashboard_supervisor.conf << 'SUPERVISOR'
[program:dashboard]
command=/home/trader/trading_bot/.venv/bin/python /home/trader/trading_bot/web_dashboard.py
directory=/home/trader/trading_bot
user=trader
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/trader/trading_bot/logs/dashboard.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=HOME="/home/trader",USER="trader"
SUPERVISOR

echo "4. Testing dashboard connectivity..."
curl -I http://127.0.0.1:5003

echo ""
echo "======================================"
echo "Nginx Configuration Files Created!"
echo "======================================"
echo ""
echo "Files created:"
echo "- /tmp/dashboard_nginx.conf (HTTP)"
echo "- /tmp/dashboard_nginx_ssl.conf (HTTPS)"
echo "- /tmp/dashboard_supervisor.conf (Supervisor)"
echo ""
echo "Next steps (run these manually):"
echo ""
echo "1. Install nginx configuration:"
echo "   sudo cp /tmp/dashboard_nginx.conf /etc/nginx/sites-available/dashboard.atcpa.co"
echo "   sudo ln -sf /etc/nginx/sites-available/dashboard.atcpa.co /etc/nginx/sites-enabled/"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo ""
echo "2. Set up DNS for dashboard.atcpa.co:"
echo "   - Add A record pointing to EC2 IP: 13.211.47.122"
echo "   - Or create CNAME record pointing to atcpa.co"
echo ""
echo "3. Test HTTP access:"
echo "   curl -I http://dashboard.atcpa.co"
echo ""
echo "4. (Optional) Setup SSL certificate:"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d dashboard.atcpa.co"
echo ""
echo "5. (Optional) Setup supervisor for process management:"
echo "   sudo cp /tmp/dashboard_supervisor.conf /etc/supervisor/conf.d/dashboard.conf"
echo "   sudo supervisorctl reread"
echo "   sudo supervisorctl update"
echo "   sudo supervisorctl status dashboard"

ENDSSH

echo ""
echo "======================================"
echo "Nginx Proxy Configuration Ready!"
echo "======================================"
echo ""
echo "Configuration files created on EC2."
echo "Follow the manual steps above to complete setup."
echo ""
echo "Quick test commands:"
echo "1. SSH into EC2"
echo "2. Run the manual commands shown above"
echo "3. Test with: curl -I http://dashboard.atcpa.co"
