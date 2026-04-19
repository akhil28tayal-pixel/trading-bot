# 🔧 EC2 Git Setup Guide

**Issue**: `fatal: not a git repository (or any of the parent directories): .git`  
**Solution**: Initialize Git on EC2 and connect to GitHub

---

## 🎯 Quick Fix (Run on EC2)

### Option 1: Automated Setup Script

**Step 1**: SSH into EC2
```bash
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com
```

**Step 2**: Run these commands on EC2
```bash
cd /home/trader/trading_bot

# Initialize Git repository
git init

# Set default branch to main
git branch -m main

# Add GitHub remote
git remote add origin https://github.com/akhil28tayal-pixel/trading-bot.git

# Fetch from GitHub
git fetch origin

# Reset to match GitHub main branch
git reset --hard origin/main

# Set upstream tracking
git branch --set-upstream-to=origin/main main

# Verify setup
git status
```

**Step 3**: Test pulling updates
```bash
git pull
```

---

## 🚀 Alternative: Deploy with Git Setup

### Option 2: Use Updated Deployment Script

I'll create an updated deployment script that includes Git initialization.

**From your local machine**:
```bash
# This will be added to deploy_ec2.sh
./deploy_ec2.sh
```

---

## 📋 Manual Step-by-Step (If Needed)

### On EC2 Instance

#### 1. Navigate to Project Directory
```bash
cd /home/trader/trading_bot
```

#### 2. Check Current State
```bash
ls -la
# You should see project files but no .git directory
```

#### 3. Initialize Git
```bash
git init
```

#### 4. Configure Git (Optional but Recommended)
```bash
git config user.name "trader"
git config user.email "trader@ec2.local"
```

#### 5. Set Main Branch
```bash
git branch -m main
```

#### 6. Add Remote Repository
```bash
git remote add origin https://github.com/akhil28tayal-pixel/trading-bot.git
```

#### 7. Verify Remote
```bash
git remote -v
# Should show:
# origin  https://github.com/akhil28tayal-pixel/trading-bot.git (fetch)
# origin  https://github.com/akhil28tayal-pixel/trading-bot.git (push)
```

#### 8. Fetch from GitHub
```bash
git fetch origin
```

#### 9. Reset to Match GitHub
```bash
git reset --hard origin/main
```

#### 10. Set Upstream Tracking
```bash
git branch --set-upstream-to=origin/main main
```

#### 11. Verify Setup
```bash
git status
# Should show: "On branch main, Your branch is up to date with 'origin/main'"

git log --oneline -5
# Should show recent commits
```

---

## ✅ Verification

### Test Git Pull
```bash
cd /home/trader/trading_bot
git pull
```

**Expected Output**:
```
Already up to date.
```

Or if there are updates:
```
Updating abc1234..def5678
Fast-forward
 file.py | 10 +++++-----
 1 file changed, 5 insertions(+), 5 deletions(-)
```

### Check Git Status
```bash
git status
```

**Expected Output**:
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

---

## 🔄 Future Updates

### Pull Latest Changes from GitHub
```bash
cd /home/trader/trading_bot
git pull
```

### Check What Changed
```bash
git log --oneline -10
```

### View Differences
```bash
git diff HEAD~1
```

### Restart Services After Update
```bash
sudo supervisorctl restart trading_bot
sudo supervisorctl restart telegram_bot
```

---

## 🛠️ Troubleshooting

### Issue: "Permission denied"
```bash
# Fix: Ensure you're the owner
sudo chown -R trader:trader /home/trader/trading_bot
```

### Issue: "Divergent branches"
```bash
# Fix: Force reset to GitHub version
git fetch origin
git reset --hard origin/main
```

### Issue: "Modified files prevent pull"
```bash
# Option 1: Stash changes
git stash
git pull
git stash pop

# Option 2: Discard local changes
git reset --hard origin/main
git pull
```

### Issue: "Remote already exists"
```bash
# Fix: Update remote URL
git remote set-url origin https://github.com/akhil28tayal-pixel/trading-bot.git
```

---

## 📝 Git Workflow on EC2

### Standard Update Process

1. **Pull latest code**
   ```bash
   cd /home/trader/trading_bot
   git pull
   ```

2. **Check what changed**
   ```bash
   git log -1 --stat
   ```

3. **Restart services**
   ```bash
   sudo supervisorctl restart all
   ```

4. **Verify services**
   ```bash
   sudo supervisorctl status
   ```

5. **Check logs**
   ```bash
   tail -f logs/main.log
   ```

---

## 🎯 Best Practices

### Before Pulling Updates
1. ✅ Check current status: `git status`
2. ✅ Backup important files if needed
3. ✅ Note current commit: `git log -1`

### After Pulling Updates
1. ✅ Verify files updated: `git log -1 --stat`
2. ✅ Check for new dependencies: `cat requirements.txt`
3. ✅ Update Python packages if needed: `pip install -r requirements.txt`
4. ✅ Restart services: `sudo supervisorctl restart all`
5. ✅ Monitor logs: `tail -f logs/main.log`

---

## 🔐 Security Notes

### Read-Only Access
The EC2 instance uses HTTPS for Git, which provides:
- ✅ Read access to public repository
- ✅ No authentication needed for pulling
- ✅ Cannot push changes (read-only)

### To Enable Push Access (Optional)
If you want to push from EC2:
1. Generate SSH key on EC2: `ssh-keygen -t ed25519`
2. Add public key to GitHub
3. Change remote to SSH: `git remote set-url origin git@github.com:akhil28tayal-pixel/trading-bot.git`

---

## 📊 Quick Reference

### Common Git Commands on EC2

```bash
# Pull latest changes
git pull

# Check status
git status

# View recent commits
git log --oneline -10

# View specific file changes
git diff filename

# Discard local changes
git checkout -- filename

# Reset to GitHub version
git reset --hard origin/main

# Check remote URL
git remote -v

# Update remote URL
git remote set-url origin https://github.com/akhil28tayal-pixel/trading-bot.git
```

---

## ✅ Summary

### What We're Doing
1. Initialize Git repository on EC2
2. Connect to GitHub repository
3. Pull latest code from GitHub
4. Enable future updates via `git pull`

### Why This Matters
- ✅ Easy updates from local machine
- ✅ Version control on EC2
- ✅ Sync with GitHub repository
- ✅ Track changes and rollback if needed

### Next Steps
1. Run the setup commands on EC2
2. Test `git pull`
3. Update deployment workflow to use Git

---

**Status**: Ready to implement  
**Time Required**: 2-3 minutes  
**Difficulty**: Easy
