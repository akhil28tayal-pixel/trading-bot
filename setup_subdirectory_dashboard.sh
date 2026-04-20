#!/bin/bash
# Setup Dashboard as Subdirectory: atcpa.co/dashboard
# No DNS required - uses existing domain

echo "Setting up Dashboard at atcpa.co/dashboard"
echo "=========================================="
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

cd /home/trader/trading_bot

echo "1. Checking current nginx configuration..."
sudo cat /etc/nginx/sites-available/atcpa.co

echo ""
echo "2. Creating updated nginx configuration with dashboard route..."
sudo tee /tmp/atcpa_co_with_dashboard.conf << 'NGINXCONF'
server {
    listen 80;
    server_name atcpa.co;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Dashboard route
    location /dashboard {
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

    # Dashboard API routes
    location /api {
        proxy_pass http://127.0.0.1:5003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Main authentication route (existing)
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINXCONF

echo ""
echo "3. Creating SSL configuration with dashboard route..."
sudo tee /tmp/atcpa_co_with_dashboard_ssl.conf << 'NGINXSSL'
server {
    listen 80;
    server_name atcpa.co;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name atcpa.co;

    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/atcpa.co/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/atcpa.co/privkey.pem;
    
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

    # Dashboard route
    location /dashboard {
        proxy_pass http://127.0.0.1:5003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Dashboard API routes
    location /api {
        proxy_pass http://127.0.0.1:5003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Main authentication route (existing)
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}
NGINXSSL

echo ""
echo "4. Testing dashboard connectivity..."
curl -I http://127.0.0.1:5003

echo ""
echo "======================================"
echo "Nginx Configuration Updated!"
echo "======================================"
echo ""
echo "Files created:"
echo "- /tmp/atcpa_co_with_dashboard.conf (HTTP)"
echo "- /tmp/atcpa_co_with_dashboard_ssl.conf (HTTPS)"
echo ""
echo "Next steps (run these manually):"
echo ""
echo "1. Backup current configuration:"
echo "   sudo cp /etc/nginx/sites-available/atcpa.co /etc/nginx/sites-available/atcpa.co.backup"
echo ""
echo "2. Update nginx configuration:"
echo "   sudo cp /tmp/atcpa_co_with_dashboard.conf /etc/nginx/sites-available/atcpa.co"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo ""
echo "3. Test dashboard access:"
echo "   curl -I http://atcpa.co/dashboard"
echo ""
echo "4. Test API access:"
echo "   curl http://atcpa.co/api/system-status"
echo ""
echo "5. (Optional) Update SSL configuration:"
echo "   sudo cp /tmp/atcpa_co_with_dashboard_ssl.conf /etc/nginx/sites-available/atcpa.co"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo ""
echo "6. Test HTTPS access:"
echo "   curl -I https://atcpa.co/dashboard"

ENDSSH

echo ""
echo "======================================"
echo "Subdirectory Dashboard Setup Complete!"
echo "======================================"
echo ""
echo "Access URLs:"
echo "- HTTP: http://atcpa.co/dashboard"
echo "- HTTPS: https://atcpa.co/dashboard (when SSL configured)"
echo ""
echo "No DNS setup required - uses existing domain!"
echo ""
echo "Routes configured:"
echo "- /dashboard -> Trading dashboard (port 5003)"
echo "- /api/* -> Dashboard API endpoints"
echo "- / -> Main authentication (port 5001)"
