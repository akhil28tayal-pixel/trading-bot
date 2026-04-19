# Nginx Proxy Setup Guide

**Setup nginx to proxy atcpa.co to Flask on port 5001**  
**Date**: April 19, 2026

---

## Overview

Configure nginx to act as a reverse proxy, routing requests from `atcpa.co` to your Flask authentication server running on `127.0.0.1:5001`.

---

## Step-by-Step Manual Setup

### **Step 1: SSH into EC2**

```bash
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com
```

### **Step 2: Install nginx**

```bash
sudo apt update
sudo apt install -y nginx
```

### **Step 3: Create nginx configuration**

```bash
sudo tee /etc/nginx/sites-available/atcpa.co << 'EOF'
server {
    listen 80;
    server_name atcpa.co;

    location / {
        proxy_pass http://127.0.0.1:5001;  # your Flask app
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle WebSocket connections if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF
```

### **Step 4: Enable the site**

```bash
sudo ln -sf /etc/nginx/sites-available/atcpa.co /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site
```

### **Step 5: Test nginx configuration**

```bash
sudo nginx -t
```

### **Step 6: Restart nginx**

```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### **Step 7: Check nginx status**

```bash
sudo systemctl status nginx
```

---

## Test the Setup

### **Step 8: Start Flask authentication server**

```bash
cd /home/trader/trading_bot
source .venv/bin/activate
python3 mobile_auth_domain_nginx.py
```

### **Step 9: Test the domain**

```bash
curl -I http://atcpa.co
```

You should see a 200 OK response from your Flask app.

---

## Update Kite Redirect URL

1. Go to https://developers.kite.trade/apps
2. Click on your app
3. Update **Redirect URL** to: `https://atcpa.co/`
4. Save changes

---

## Telegram Integration

The updated `/auth` command now uses the nginx proxy setup:

- **Domain**: `atcpa.co`
- **URL**: `https://atcpa.co/`
- **Proxy**: nginx -> `http://127.0.0.1:5001`

---

## Benefits of Nginx Proxy

### **Professional Setup**
- Standard web server configuration
- Better performance and caching
- SSL termination support
- Load balancing ready

### **Security**
- Security headers automatically added
- Rate limiting capabilities
- DDoS protection
- Request logging

### **Flexibility**
- Easy to add SSL certificates
- Multiple domains support
- URL rewriting capabilities
- Static file serving

---

## Troubleshooting

### **Nginx not starting**
```bash
# Check logs
sudo journalctl -u nginx

# Check configuration
sudo nginx -t

# Check if port 80 is free
sudo netstat -tulpn | grep :80
```

### **Proxy not working**
```bash
# Check if Flask is running on port 5001
netstat -tulpn | grep 5001

# Test Flask directly
curl http://127.0.0.1:5001

# Check nginx error log
sudo tail -f /var/log/nginx/error.log
```

### **Domain not resolving**
```bash
# Check DNS
nslookup atcpa.co

# Check if domain points to EC2
ping atcpa.co
```

---

## SSL Certificate Setup (Future)

When ready to add HTTPS:

### **Install Certbot**
```bash
sudo apt install certbot python3-certbot-nginx
```

### **Get SSL Certificate**
```bash
sudo certbot --nginx -d atcpa.co
```

### **Auto-renew SSL**
```bash
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## Summary

After completing these steps:

1. **nginx** proxies `atcpa.co` to Flask on port 5001
2. **Flask** handles Kite authentication callbacks
3. **Telegram** sends authentication instructions
4. **Kite** redirects to `https://atcpa.co/`
5. **Token** is saved automatically

This provides a professional, production-ready authentication setup!
