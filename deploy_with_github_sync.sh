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
