# Manual SSL Setup Guide for atcpa.co

**Complete manual SSL configuration for permanent HTTPS**  
**Date**: April 19, 2026

---

## Current Status

- nginx configuration created but not activated (sudo required)
- SSL certificate not obtained (sudo required)
- HTTP to HTTPS redirect configured but not working

---

## Manual Setup Steps

### **Step 1: SSH into EC2**

```bash
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com
```

### **Step 2: Install certbot**

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

### **Step 3: Create nginx SSL configuration**

```bash
sudo tee /etc/nginx/sites-available/atcpa.co << 'EOF'
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
EOF
```

### **Step 4: Enable SSL site**

```bash
sudo ln -sf /etc/nginx/sites-available/atcpa.co /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

### **Step 5: Test nginx configuration**

```bash
sudo nginx -t
```

### **Step 6: Get SSL certificate**

```bash
sudo certbot --nginx -d atcpa.co --non-interactive --agree-tos --email admin@atcpa.co
```

### **Step 7: Set up auto-renewal**

```bash
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### **Step 8: Reload nginx**

```bash
sudo systemctl reload nginx
```

---

## Alternative: Use Existing SSL Certificate

If you already have SSL certificates for atcpa.co, use this configuration:

### **Step 1: Place certificates**

```bash
# Copy your certificates to nginx locations
sudo cp /path/to/your/certificate.crt /etc/ssl/certs/atcpa.co.crt
sudo cp /path/to/your/private.key /etc/ssl/private/atcpa.co.key
sudo chmod 600 /etc/ssl/private/atcpa.co.key
```

### **Step 2: Create nginx config with your certificates**

```bash
sudo tee /etc/nginx/sites-available/atcpa.co << 'EOF'
server {
    listen 80;
    server_name atcpa.co;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name atcpa.co;

    # Your SSL certificates
    ssl_certificate /etc/ssl/certs/atcpa.co.crt;
    ssl_certificate_key /etc/ssl/private/atcpa.co.key;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

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
EOF
```

---

## Testing the Setup

### **Test HTTP to HTTPS redirect:**

```bash
curl -I http://atcpa.co
# Should show 301 redirect to HTTPS
```

### **Test HTTPS:**

```bash
curl -I https://atcpa.co
# Should show 200 OK with SSL
```

### **Test Flask app:**

```bash
curl https://atcpa.co
# Should show Flask app response
```

---

## Update Kite Redirect URL

After SSL is working:

1. Go to https://developers.kite.trade/apps
2. Update redirect URL to: `https://atcpa.co/`
3. Save changes

---

## Troubleshooting

### **502 Bad Gateway:**
- Flask app not running on port 5001
- Check: `ps aux | grep python`

### **SSL Certificate Error:**
- Certificate not found or expired
- Check: `sudo certbot certificates`

### **nginx Configuration Error:**
- Syntax error in config
- Check: `sudo nginx -t`

### **Port 443 not accessible:**
- Firewall blocking HTTPS
- Check AWS Security Group allows port 443

---

## Quick Test Commands

```bash
# Check nginx status
sudo systemctl status nginx

# Check SSL certificates
sudo certbot certificates

# Test nginx config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Test Flask app
curl http://127.0.0.1:5001

# Test HTTPS proxy
curl https://atcpa.co
```

---

## Final Result

After completing these steps:

- HTTP automatically redirects to HTTPS
- SSL certificate installed and auto-renews
- Flask app accessible via HTTPS
- Kite redirect URL works with HTTPS
- Professional permanent setup

Complete the manual setup and enjoy permanent HTTPS!
