# Subdirectory Dashboard Setup Commands

**Quick setup for atcpa.co/dashboard routing**  
**No DNS required - uses existing domain**

---

## Manual Setup Commands

### **Step 1: SSH into EC2**

```bash
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com
```

### **Step 2: Backup Current Configuration**

```bash
sudo cp /etc/nginx/sites-available/atcpa.co /etc/nginx/sites-available/atcpa.co.backup
```

### **Step 3: Update Nginx Configuration**

```bash
sudo cp /tmp/atcpa_co_with_dashboard.conf /etc/nginx/sites-available/atcpa.co
sudo nginx -t
sudo systemctl reload nginx
```

### **Step 4: Test Dashboard Access**

```bash
# Test dashboard route
curl -I http://atcpa.co/dashboard

# Test API access
curl http://atcpa.co/api/system-status

# Test main authentication (should still work)
curl -I http://atcpa.co
```

### **Step 5: (Optional) Update SSL Configuration**

```bash
sudo cp /tmp/atcpa_co_with_dashboard_ssl.conf /etc/nginx/sites-available/atcpa.co
sudo nginx -t
sudo systemctl reload nginx

# Test HTTPS access
curl -I https://atcpa.co/dashboard
```

---

## Expected Results

### **After Setup:**
- **Dashboard**: `http://atcpa.co/dashboard` 
- **API**: `http://atcpa.co/api/*`
- **Authentication**: `http://atcpa.co/` (unchanged)

### **HTTPS Access:**
- **Dashboard**: `https://atcpa.co/dashboard`
- **API**: `https://atcpa.co/api/*`
- **Authentication**: `https://atcpa.co/` (unchanged)

---

## Configuration Details

### **Routes Configured:**
```
/dashboard -> Trading dashboard (port 5003)
/api/* -> Dashboard API endpoints
/ -> Main authentication (port 5001)
```

### **Nginx Configuration:**
```nginx
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
    # ... same proxy settings
}

# Main authentication route (unchanged)
location / {
    proxy_pass http://127.0.0.1:5001;
    # ... same proxy settings
}
```

---

## Troubleshooting

### **If Dashboard Doesn't Load:**
```bash
# Check nginx status
sudo systemctl status nginx

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check if dashboard is running
ps aux | grep web_dashboard

# Test direct dashboard access
curl -I http://127.0.0.1:5003
```

### **If API Doesn't Work:**
```bash
# Test API endpoint directly
curl http://127.0.0.1:5003/api/system-status

# Check nginx configuration
sudo nginx -t

# Reload nginx if needed
sudo systemctl reload nginx
```

### **If Main Authentication Breaks:**
```bash
# Test main authentication
curl -I http://127.0.0.1:5001

# Restore backup if needed
sudo cp /etc/nginx/sites-available/atcpa.co.backup /etc/nginx/sites-available/atcpa.co
sudo systemctl reload nginx
```

---

## Quick Copy-Paste Commands

### **Complete Setup (Copy & Paste):**

```bash
# SSH into EC2 first, then run:

# 1. Backup current config
sudo cp /etc/nginx/sites-available/atcpa.co /etc/nginx/sites-available/atcpa.co.backup

# 2. Update nginx configuration
sudo cp /tmp/atcpa_co_with_dashboard.conf /etc/nginx/sites-available/atcpa.co
sudo nginx -t
sudo systemctl reload nginx

# 3. Test all routes
curl -I http://atcpa.co/dashboard
curl http://atcpa.co/api/system-status
curl -I http://atcpa.co

# 4. (Optional) Update SSL
sudo cp /tmp/atcpa_co_with_dashboard_ssl.conf /etc/nginx/sites-available/atcpa.co
sudo nginx -t
sudo systemctl reload nginx
curl -I https://atcpa.co/dashboard
```

---

## Benefits of Subdirectory Setup

### **Advantages:**
- **No DNS required** - uses existing domain
- **Single SSL certificate** - covers all routes
- **Clean URLs** - professional appearance
- **Easy access** - no subdomain management
- **Unified domain** - consistent branding

### **URL Structure:**
```
https://atcpa.co/           - Main authentication
https://atcpa.co/dashboard  - Trading dashboard
https://atcpa.co/api/*      - API endpoints
```

---

## Summary

1. **Configuration files created** on EC2
2. **Manual setup required** (sudo permissions)
3. **No DNS needed** - uses existing domain
4. **Clean URL structure** - professional appearance
5. **Easy to test** - immediate verification

**Run the manual commands above to enable dashboard access at atcpa.co/dashboard!**
