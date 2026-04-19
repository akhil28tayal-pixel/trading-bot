#!/bin/bash
"""
Fix SSH Connection to EC2 Instance
Troubleshoot and fix SSH key issues
"""

EC2_HOST="ubuntu@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com"

echo "🔧 Fixing SSH Connection to EC2..."
echo "📍 Target: $EC2_HOST"

# 1. Check for SSH keys
echo "1. Checking for SSH keys..."
if [ -d ~/.ssh ]; then
    echo "   SSH directory found: ~/.ssh"
    echo "   Available keys:"
    ls -la ~/.ssh/*.pem 2>/dev/null || echo "   No .pem files found"
    ls -la ~/.ssh/id_* 2>/dev/null || echo "   No id_* files found"
else
    echo "   ❌ No SSH directory found"
fi

# 2. Check for AWS key pairs
echo "2. Checking for AWS key pairs..."
if [ -d ~/.aws ]; then
    echo "   AWS directory found: ~/.aws"
    ls -la ~/.aws/ 2>/dev/null
fi

# 3. Check for common key locations
echo "3. Checking common key locations..."
KEY_LOCATIONS=(
    "~/.ssh/id_rsa"
    "~/.ssh/id_ed25519"
    "~/.ssh/ec2-key.pem"
    "~/Downloads/*.pem"
    "~/Desktop/*.pem"
)

for location in "${KEY_LOCATIONS[@]}"; do
    expanded_location="${location/#\~/$HOME}"
    if [ -f "$expanded_location" ]; then
        echo "   ✅ Found: $expanded_location"
    fi
done

# 4. Test SSH connection with different methods
echo "4. Testing SSH connection methods..."

# Method 1: Default SSH
echo "   Testing default SSH..."
ssh -o ConnectTimeout=5 -o BatchMode=yes $EC2_HOST "echo 'SSH successful'" 2>&1 || echo "   ❌ Default SSH failed"

# Method 2: Try with common key files
echo "   Testing with common keys..."
for key in ~/.ssh/id_rsa ~/.ssh/id_ed25519 ~/.ssh/ec2-key.pem ~/Downloads/*.pem; do
    if [ -f "$key" ]; then
        echo "   Trying key: $key"
        ssh -i "$key" -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no $EC2_HOST "echo 'SSH successful'" 2>&1 && {
            echo "   ✅ SSH successful with key: $key"
            echo "   Use this key for deployment"
            exit 0
        }
    fi
done

# 5. Provide manual instructions
echo "5. Manual SSH Configuration"
echo "   If automated methods failed, try these manual steps:"
echo ""
echo "   Option 1: Use specific key file"
echo "   ssh -i /path/to/your-key.pem ubuntu@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com"
echo ""
echo "   Option 2: Add key to SSH config"
echo "   Add to ~/.ssh/config:"
echo "   Host ec2-trading-bot"
echo "       HostName ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com"
echo "       User ubuntu"
echo "       IdentityFile /path/to/your-key.pem"
echo ""
echo "   Option 3: Update deployment script with key path"
echo "   Edit deploy_to_ec2.sh and add:"
echo "   SSH_KEY='/path/to/your-key.pem'"
echo "   Then use: ssh -i \$SSH_KEY \$EC2_HOST"
echo ""

# 6. Check EC2 instance status
echo "6. EC2 Instance Checklist"
echo "   Verify these items:"
echo "   ✅ EC2 instance is running in AWS Console"
echo "   ✅ Security group allows SSH (port 22) from your IP"
echo "   ✅ You have the correct SSH key (.pem file)"
echo "   ✅ SSH key permissions are correct (chmod 400 key.pem)"
echo "   ✅ Key pair matches the one used to launch instance"

echo ""
echo "🔧 SSH Troubleshooting Complete"
echo "📋 Next Steps:"
echo "   1. Identify your SSH key file"
echo "   2. Test SSH manually: ssh -i /path/to/key.pem ubuntu@EC2_HOST"
echo "   3. Update deployment script with correct key path"
echo "   4. Run deployment again"
