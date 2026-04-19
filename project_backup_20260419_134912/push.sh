#!/bin/bash
"""
One-Command Push to Production
Ultra-simple deployment script
"""

echo "🚀 Pushing to production..."
./deployment/upload_code.sh 159.89.171.105 && echo "✅ Code pushed successfully!"
