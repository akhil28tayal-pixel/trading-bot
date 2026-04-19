#!/bin/bash
# Complete Nginx SSL Setup for atcpa.co
# Permanent HTTPS configuration with SSL certificate

echo "Setting up Nginx with SSL for atcpa.co"
echo "======================================="
echo "This will configure permanent HTTPS setup"
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "1. Installing certbot for SSL certificates..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

echo ""
echo "2. Creating nginx SSL configuration..."
sudo tee /etc/nginx/sites-available/atcpa.co << 'NGINXSSL'
server {
    listen 80;
    server_name atcpa.co;

    # Redirect all HTTP to HTTPS
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
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    location / {
        proxy_pass http://127.0.0.1:5001;  # Flask app
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
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINXSSL

echo ""
echo "3. Enabling SSL site..."
sudo ln -sf /etc/nginx/sites-available/atcpa.co /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo ""
echo "4. Testing nginx configuration..."
sudo nginx -t

echo ""
echo "5. Reloading nginx..."
sudo systemctl reload nginx

echo ""
echo "6. Getting SSL certificate..."
sudo certbot --nginx -d atcpa.co --non-interactive --agree-tos --email admin@atcpa.co

echo ""
echo "7. Setting up SSL auto-renewal..."
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

echo ""
echo "8. Testing HTTPS configuration..."
sudo systemctl status nginx --no-pager

ENDSSH

echo ""
echo "======================================"
echo "SSL Setup Complete!"
echo "======================================"
echo ""
echo "Testing HTTPS configuration..."
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSLTEST'

echo "Testing HTTP to HTTPS redirect..."
curl -I http://atcpa.co

echo ""
echo "Testing HTTPS directly..."
curl -I https://atcpa.co

echo ""
echo "Testing Flask app through HTTPS proxy..."
curl -s https://atcpa.co | head -5

ENDSSLTEST

echo ""
echo "======================================"
echo "SSL Configuration Complete!"
echo "======================================"
echo ""
echo "Your domain now has permanent HTTPS!"
echo "HTTP automatically redirects to HTTPS"
echo "SSL certificate auto-renews daily"
echo ""
echo "Update Kite redirect URL to: https://atcpa.co/"
