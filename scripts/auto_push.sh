#!/bin/bash
# Auto-push script for trading bot
# Automatically commits and pushes changes to GitHub

# Check if there are changes to commit
if [ -n "$(git status --porcelain)" ]; then
    echo "Changes detected, pushing to GitHub..."
    
    # Add all changes
    git add .
    
    # Commit with timestamp
    git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Push to GitHub
    git push origin main
    
    echo "Changes pushed successfully!"
else
    echo "No changes to push"
fi
