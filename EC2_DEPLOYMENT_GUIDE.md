# AWS EC2 Deployment Guide

## 🎯 Overview
Complete guide to deploy your trading bot to AWS EC2 instance.

**Target Server:** `ubuntu@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com`

---

## 🚀 Quick Deployment

### **Step 1: Run Deployment Script**
```bash
chmod +x deploy_to_ec2.sh
./deploy_to_ec2.sh
```

### **Step 2: Configure on EC2**
```bash
# SSH to EC2
ssh ubuntu@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com

# Configure API keys
nano /home/ubuntu/trading_bot/.env

# Setup supervisor
sudo /home/ubuntu/trading_bot/setup_supervisor.sh

# Setup authentication
/home/ubuntu/trading_bot/setup_auth.sh

# Start the bot
sudo supervisorctl start trading_system
```

---

## 📋 Detailed Steps

### **1. Pre-Deployment Checklist**

**EC2 Requirements:**
- ✅ EC2 instance running Ubuntu
- ✅ SSH access configured
- ✅ Security group allows SSH (port 22)
- ✅ Security group allows HTTP (port 5001 for auth)

**Local Requirements:**
- ✅ SSH key configured for EC2
- ✅ Project ready for deployment

### **2. Environment Configuration**

Edit `/home/ubuntu/trading_bot/.env` on EC2:

```bash
# Kite Connect API Configuration
KITE_API_KEY="your_api_key_here"
KITE_API_SECRET="your_api_secret_here"
KITE_ACCESS_TOKEN=""  # Will be set after authentication

# Trading Configuration
TRADING_MODE="PAPER"
TRADING_CAPITAL=100000
RISK_PER_TRADE=0.01
DAILY_LOSS_LIMIT=0.03
PAPER_TRADING=true

# Telegram Configuration
TELEGRAM_BOT_TOKEN="your_telegram_token"
TELEGRAM_CHAT_ID="your_chat_id"

# Execution Settings
ENABLE_SLIPPAGE=true
SLIPPAGE_PERCENT=0.003
ENABLE_DELAY=true
EXECUTION_DELAY_MS=200
ENABLE_VOLATILITY_ADJUSTMENT=true
ENABLE_TIME_BASED_SLIPPAGE=true
ENABLE_PARTIAL_FILLS=false
```

### **3. Authentication Setup**

```bash
# On EC2, run authentication setup
cd /home/ubuntu/trading_bot
./setup_auth.sh
```

**Authentication Process:**
1. Script starts Flask server on port 5001
2. Access: `http://EC2_PUBLIC_IP:5001`
3. Complete Kite login process
4. Token automatically saved to `.env`

### **4. Supervisor Management**

```bash
# Setup supervisor (one-time)
sudo /home/ubuntu/trading_bot/setup_supervisor.sh

# Management commands
sudo supervisorctl status
sudo supervisorctl start trading_system
sudo supervisorctl stop trading_system
sudo supervisorctl restart trading_system
```

### **5. Monitoring**

```bash
# Run monitoring script
/home/ubuntu/trading_bot/monitor.sh

# View logs
tail -f /home/ubuntu/trading_bot/logs/supervisor.log
tail -f /home/ubuntu/trading_bot/logs/telegram_bot.log

# Check processes
ps aux | grep python | grep trading_bot
```

---

## 🔧 Management Commands

### **Deployment Commands**
```bash
# Deploy from local
./deploy_to_ec2.sh

# Update code only (from local)
scp -r . ubuntu@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com:/home/ubuntu/trading_bot/
```

### **EC2 Management Commands**
```bash
# SSH to EC2
ssh ubuntu@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com

# Bot management
sudo supervisorctl status
sudo supervisorctl restart trading_system

# View logs
tail -f /home/ubuntu/trading_bot/logs/supervisor.log

# Monitor system
/home/ubuntu/trading_bot/monitor.sh

# Check configuration
cat /home/ubuntu/trading_bot/.env
```

### **Troubleshooting Commands**
```bash
# Check if bot is running
ps aux | grep python | grep trading_bot

# Check supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Restart everything
sudo supervisorctl restart all

# Check system resources
free -h
df -h
top
```

---

## 🛡️ Security Configuration

### **EC2 Security Group**
Required inbound rules:
- **SSH (22):** Your IP address
- **HTTP (5001):** Your IP address (for authentication)
- **HTTPS (443):** 0.0.0.0/0 (for API calls)

### **Environment Variables**
- All sensitive data stored in `.env` file
- File permissions: `600` (owner read/write only)
- Never commit `.env` to version control

---

## 📊 Expected Results

### **Successful Deployment**
```
trading_system:trading_bot       RUNNING   pid 1234, uptime 0:01:23
trading_system:telegram_bot      RUNNING   pid 1235, uptime 0:01:23
```

### **Bot Functionality**
- ✅ Continuous operation (24/7)
- ✅ Market hours detection
- ✅ Paper trading mode
- ✅ Telegram bot responsive
- ✅ Authentication working
- ✅ Logs being generated

---

## 🚨 Troubleshooting

### **Common Issues**

**1. SSH Connection Failed**
```bash
# Check EC2 instance status
# Verify security group settings
# Confirm SSH key configuration
```

**2. Authentication Issues**
```bash
# Check if port 5001 is accessible
# Verify API keys in .env file
# Check Flask server logs
```

**3. Bot Not Starting**
```bash
# Check supervisor logs
tail -f /home/ubuntu/trading_bot/logs/supervisor.log

# Verify Python dependencies
source /home/ubuntu/trading_bot/.venv/bin/activate
pip list

# Check configuration
python3 -c "import config; print(config.API_KEY)"
```

**4. Telegram Bot Not Responding**
```bash
# Check telegram bot logs
tail -f /home/ubuntu/trading_bot/logs/telegram_bot.log

# Verify telegram configuration
grep TELEGRAM /home/ubuntu/trading_bot/.env
```

---

## 📈 Next Steps

### **After Successful Deployment**
1. **Test all functionality** - Run through all bot commands
2. **Monitor for 24 hours** - Ensure stable operation
3. **Set up alerts** - Configure monitoring alerts
4. **Backup configuration** - Save your `.env` file securely

### **Production Readiness**
1. **Switch to LIVE mode** - Change `TRADING_MODE="LIVE"`
2. **Reduce risk** - Adjust `RISK_PER_TRADE` if needed
3. **Monitor closely** - Watch first live trades carefully
4. **Scale resources** - Upgrade EC2 instance if needed

---

**🎉 Your trading bot is now deployed on AWS EC2 and ready for operation!**
