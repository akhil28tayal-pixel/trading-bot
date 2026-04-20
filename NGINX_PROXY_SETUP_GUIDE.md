# Nginx Proxy Setup Guide for Dashboard

**Complete manual setup for nginx proxy configuration**  
**Date**: April 20, 2026

---

## Current Status

### **Dashboard Status:**
- **Running**: Yes (PID: 30985)
- **Port**: 5003 (127.0.0.1)
- **Health**: Responding with HTTP 200
- **Configuration**: Ready for nginx proxy

### **Configuration Files:**
- **HTTP config**: `/tmp/dashboard_nginx.conf` (created)
- **HTTPS config**: `/tmp/dashboard_nginx_ssl.conf` (created)
- **Supervisor config**: `/tmp/dashboard_supervisor.conf` (created)

---

## Manual Setup Steps

### **Step 1: SSH into EC2**

```bash
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com
```

### **Step 2: Install nginx Configuration**

```bash
# Copy nginx configuration
sudo cp /tmp/dashboard_nginx.conf /etc/nginx/sites-available/dashboard.atcpa.co

# Enable the site
sudo ln -sf /etc/nginx/sites-available/dashboard.atcpa.co /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### **Step 3: Set up DNS for dashboard.atcpa.co**

**Option A: A Record (Recommended)**
```
Type: A
Name: dashboard.atcpa.co
Value: 13.211.47.122
TTL: 300 (or default)
```

**Option B: CNAME Record**
```
Type: CNAME
Name: dashboard.atcpa.co
Value: atcpa.co
TTL: 300 (or default)
```

### **Step 4: Test HTTP Access**

```bash
# Test nginx proxy
curl -I http://dashboard.atcpa.co

# Expected response:
# HTTP/1.1 200 OK
# Server: nginx/1.24.0 (Ubuntu)
# Content-Type: text/html; charset=utf-8
```

### **Step 5: (Optional) Setup SSL Certificate**

```bash
# Install certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d dashboard.atcpa.co --non-interactive --agree-tos --email admin@atcpa.co

# Test HTTPS
curl -I https://dashboard.atcpa.co
```

### **Step 6: (Optional) Setup Supervisor for Process Management**

```bash
# Copy supervisor configuration
sudo cp /tmp/dashboard_supervisor.conf /etc/supervisor/conf.d/dashboard.conf

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Check status
sudo supervisorctl status dashboard

# Restart dashboard with supervisor
sudo supervisorctl restart dashboard
```

---

## Configuration Details

### **HTTP Nginx Configuration**
```nginx
server {
    listen 80;
    server_name dashboard.atcpa.co;

    location / {
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
}
```

### **Supervisor Configuration**
```ini
[program:dashboard]
command=/home/trader/trading_bot/.venv/bin/python /home/trader/trading_bot/web_dashboard.py
directory=/home/trader/trading_bot
user=trader
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/trader/trading_bot/logs/dashboard.log
```

---

## Troubleshooting

### **Common Issues and Solutions**

#### **1. DNS Not Resolving**
```bash
# Check DNS resolution
nslookup dashboard.atcpa.co
dig dashboard.atcpa.co

# If not resolving, wait for DNS propagation (5-30 minutes)
# Or test with local hosts file:
echo "13.211.47.122 dashboard.atcpa.co" | sudo tee -a /etc/hosts
```

#### **2. Nginx Configuration Error**
```bash
# Check nginx syntax
sudo nginx -t

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check if site is enabled
ls -la /etc/nginx/sites-enabled/ | grep dashboard
```

#### **3. Dashboard Not Responding**
```bash
# Check if dashboard is running
ps aux | grep web_dashboard

# Check if port 5003 is listening
ss -tulpn | grep 5003

# Test direct access
curl -I http://127.0.0.1:5003

# Restart dashboard
pkill -f web_dashboard
cd /home/trader/trading_bot
source .venv/bin/activate
nohup python3 web_dashboard.py > logs/dashboard.log 2>&1 &
```

#### **4. SSL Certificate Issues**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
sudo nginx -t
sudo systemctl reload nginx
```

---

## Quick Setup Commands

### **Copy and Paste These Commands:**

```bash
# SSH into EC2 first, then run:

# 1. Install nginx configuration
sudo cp /tmp/dashboard_nginx.conf /etc/nginx/sites-available/dashboard.atcpa.co
sudo ln -sf /etc/nginx/sites-available/dashboard.atcpa.co /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 2. Test configuration
curl -I http://dashboard.atcpa.co

# 3. (Optional) Setup SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d dashboard.atcpa.co --non-interactive --agree-tos --email admin@atcpa.co

# 4. (Optional) Setup supervisor
sudo cp /tmp/dashboard_supervisor.conf /etc/supervisor/conf.d/dashboard.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status dashboard
```

---

## Expected Results

### **After Setup:**
- **HTTP Access**: `http://dashboard.atcpa.co` works
- **Dashboard Loads**: Full trading dashboard interface
- **Real-time Data**: Trading data updates every 30 seconds
- **Professional URL**: Clean domain-based access

### **With SSL:**
- **HTTPS Access**: `https://dashboard.atcpa.co` works
- **Auto-redirect**: HTTP automatically redirects to HTTPS
- **Secure Connection**: SSL certificate installed and valid

### **With Supervisor:**
- **Auto-restart**: Dashboard restarts if it crashes
- **Process Management**: Managed by supervisor
- **Log Management**: Logs rotated and managed

---

## Security Considerations

### **Current Setup:**
- **Internal Only**: Dashboard only accessible via domain
- **No Auth**: No authentication required (consider adding)
- **HTTPS Ready**: SSL configuration prepared

### **Recommendations:**
1. **Add Authentication**: Implement login/password
2. **IP Whitelisting**: Restrict access to specific IPs
3. **Rate Limiting**: Prevent abuse
4. **SSL Certificate**: Always use HTTPS in production

---

## Alternative Access Methods

### **If DNS Setup Fails:**

#### **1. IP-based Access**
```bash
# Add to nginx config:
server {
    listen 80;
    server_name 13.211.47.122;
    # ... same configuration
}
```

#### **2. Subdirectory Access**
```bash
# Add to main atcpa.co config:
location /dashboard {
    proxy_pass http://127.0.0.1:5003;
    # ... same proxy settings
}
```

#### **3. SSH Tunnel (Always Works)**
```bash
# Create SSH tunnel:
ssh -i ~/Downloads/trading-bot.pem -L 8080:127.0.0.1:5003 trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com

# Access via: http://localhost:8080
```

---

## Summary

1. **Configuration files are ready** on EC2
2. **Manual setup required** due to sudo permissions
3. **DNS setup needed** for dashboard.atcpa.co
4. **Optional SSL** for secure access
5. **Optional supervisor** for process management

**Complete the manual steps above to enable domain-based access to your trading dashboard!**
