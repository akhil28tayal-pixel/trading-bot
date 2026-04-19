#!/bin/bash
"""
GitHub Repository Setup Script
Creates GitHub repo and sets up automatic pushing
"""

# Configuration
REPO_NAME="trading-bot"
GITHUB_USERNAME="YOUR_GITHUB_USERNAME"  # Change this to your GitHub username
DESCRIPTION="Advanced Options Trading Bot with Backtesting"

echo "GitHub Repository Setup for Trading Bot"
echo "====================================="

# Step 1: Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo "GitHub CLI found"
    USE_GH_CLI=true
else
    echo "GitHub CLI not found, will use manual setup"
    USE_GH_CLI=false
fi

# Step 2: Create GitHub repository
echo "Step 2: Creating GitHub repository..."

if [ "$USE_GH_CLI" = true ]; then
    echo "Using GitHub CLI to create repository..."
    
    # Create repository using GitHub CLI
    gh repo create $GITHUB_USERNAME/$REPO_NAME \
        --public \
        --description "$DESCRIPTION" \
        --source=. \
        --push \
        --set-default
    
    if [ $? -eq 0 ]; then
        echo "Repository created successfully using GitHub CLI"
    else
        echo "GitHub CLI failed, falling back to manual setup"
        USE_GH_CLI=false
    fi
fi

if [ "$USE_GH_CLI" = false ]; then
    echo "Manual GitHub setup required:"
    echo ""
    echo "1. Go to https://github.com and sign in"
    echo "2. Click the '+' button in the top right and select 'New repository'"
    echo "3. Repository name: $REPO_NAME"
    echo "4. Description: $DESCRIPTION"
    echo "5. Make it Public"
    echo "6. DO NOT initialize with README (we already have one)"
    echo "7. Click 'Create repository'"
    echo ""
    echo "8. After creation, run these commands:"
    echo "   git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    echo "   git push -u origin main"
    echo ""
    echo "Replace $GITHUB_USERNAME with your actual GitHub username"
fi

# Step 3: Set up Git configuration
echo "Step 3: Setting up Git configuration..."

# Configure Git user if not set
if [ -z "$(git config user.name)" ]; then
    echo "Please enter your Git user name:"
    read -r GIT_NAME
    git config --global user.name "$GIT_NAME"
fi

if [ -z "$(git config user.email)" ]; then
    echo "Please enter your Git email:"
    read -r GIT_EMAIL
    git config --global user.email "$GIT_EMAIL"
fi

echo "Git configuration:"
echo "Name: $(git config user.name)"
echo "Email: $(git config user.email)"

# Step 4: Create auto-push script
echo "Step 4: Creating auto-push script..."

cat > auto_push.sh << 'EOF'
#!/bin/bash
"""
Auto-push script for trading bot
Automatically commits and pushes changes to GitHub
"""

# Check if there are changes to commit
if [ -n "$(git status --porcelain)" ]; then
    echo "Changes detected, pushing to GitHub..."
    
    # Add all changes
    git add .
    
    # Commit with timestamp
    git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M:%S')

    # Push to GitHub
    git push origin main
    
    echo "Changes pushed successfully!"
else
    echo "No changes to push"
fi
EOF

chmod +x auto_push.sh

# Step 5: Create Git hook for auto-push
echo "Step 5: Setting up Git hooks..."

mkdir -p .git/hooks

cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
"""
Post-commit hook to automatically push to GitHub
"""

echo "Pushing changes to GitHub..."
git push origin main
EOF

chmod +x .git/hooks/post-commit

# Step 6: Create deployment script with GitHub sync
echo "Step 6: Creating deployment script with GitHub sync..."

cat > deploy_with_github_sync.sh << 'EOF'
#!/bin/bash
"""
Deploy to EC2 with GitHub sync
"""

echo "Deploying to EC2 with GitHub sync..."

# 1. Push changes to GitHub
./auto_push.sh

# 2. Deploy to EC2
./deploy_ec2.sh

echo "Deployment complete with GitHub sync!"
EOF

chmod +x deploy_with_github_sync.sh

# Step 7: Create GitHub Actions workflow
echo "Step 7: Setting up GitHub Actions..."

mkdir -p .github/workflows

cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy to EC2

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to EC2
      run: |
        echo "Deploying to EC2..."
        # Add your deployment commands here
        echo "Deployment complete"
EOF

echo ""
echo "GitHub Setup Complete!"
echo "===================="
echo ""
echo "Next Steps:"
echo "1. If you used GitHub CLI: Repository is already created and pushed"
echo "2. If manual setup: Create repo on GitHub and run:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/trading-bot.git"
echo "   git push -u origin main"
echo ""
echo "3. Auto-push options:"
echo "   - Run './auto_push.sh' to push changes"
echo "   - Git hooks will auto-push after each commit"
echo "   - Use './deploy_with_github_sync.sh' for deployment with sync"
echo ""
echo "4. GitHub Actions workflow created for CI/CD"
echo ""
echo "Your trading bot is now ready for GitHub integration!"
