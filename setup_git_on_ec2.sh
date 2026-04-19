#!/bin/bash
# Setup Git on EC2 and Pull from GitHub
# Run this script on EC2 to initialize Git and pull latest code

set -e

echo "🔧 Setting up Git on EC2"
echo "======================="
echo ""

# Configuration
GITHUB_REPO="https://github.com/akhil28tayal-pixel/trading-bot.git"
PROJECT_DIR="/home/trader/trading_bot"

echo "📍 Current directory: $(pwd)"
echo "📦 GitHub repository: $GITHUB_REPO"
echo ""

# Check if we're in the project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    echo "Creating directory..."
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Check if .git exists
if [ -d ".git" ]; then
    echo "✅ Git repository already initialized"
    echo "📥 Pulling latest changes..."
    git pull origin main
else
    echo "🔧 Initializing Git repository..."
    
    # Initialize git
    git init
    
    # Set default branch to main
    git branch -m main
    
    # Add remote
    echo "🔗 Adding remote repository..."
    git remote add origin "$GITHUB_REPO"
    
    # Fetch from remote
    echo "📥 Fetching from GitHub..."
    git fetch origin
    
    # Reset to match remote
    echo "🔄 Resetting to match remote main branch..."
    git reset --hard origin/main
    
    # Set upstream
    git branch --set-upstream-to=origin/main main
    
    echo "✅ Git repository initialized and synced with GitHub"
fi

echo ""
echo "📊 Git Status:"
git status

echo ""
echo "📝 Recent Commits:"
git log --oneline -5

echo ""
echo "✅ Git setup complete!"
echo ""
echo "🔄 To pull updates in the future, run:"
echo "   cd $PROJECT_DIR && git pull"
