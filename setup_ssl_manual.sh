#!/bin/bash
# Manual SSL Setup - Alternative Approach
# Uses existing SSL certificate files

echo "Manual SSL Setup for atcpa.co"
echo "=============================="
echo "This script will help you manually configure SSL"
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "Creating SSL configuration file..."
cat > /tmp/nginx_ssl_config.conf << 'NGINXCONF'
server {
    listen 80;
    server_name atcpa.co;

    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name atcpa.co;

    # SSL Configuration - UPDATE THESE PATHS
    ssl_certificate /etc/ssl/certs/atcpa.co.crt;
    ssl_certificate_key /etc/ssl/private/atcpa.co.key;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

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
    }
}
NGINXCONF

echo ""
echo "SSL configuration file created: /tmp/nginx_ssl_config.conf"
echo ""
echo "Next steps (run these manually):"
echo "1. Copy your SSL certificates:"
echo "   sudo cp /path/to/your/certificate.crt /etc/ssl/certs/atcpa.co.crt"
echo "   sudo cp /path/to/your/private.key /etc/ssl/private/atcpa.co.key"
echo "   sudo chmod 600 /etc/ssl/private/atcpa.co.key"
echo ""
echo "2. Install nginx configuration:"
echo "   sudo cp /tmp/nginx_ssl_config.conf /etc/nginx/sites-available/atcpa.co"
echo "   sudo ln -sf /etc/nginx/sites-available/atcpa.co /etc/nginx/sites-enabled/"
echo "   sudo rm -f /etc/nginx/sites-enabled/default"
echo ""
echo "3. Test and reload nginx:"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo ""
echo "4. Test HTTPS:"
echo "   curl -I https://atcpa.co"

ENDSSH

echo ""
echo "======================================"
echo "Manual SSL Setup Instructions Ready!"
echo "======================================"
echo ""
echo "SSH into EC2 and run the commands shown above"
echo "Or use certbot for automatic SSL certificates"
