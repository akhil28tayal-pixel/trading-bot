#!/usr/bin/env python3
"""
Manual Authentication Script
Use this when automatic authentication fails
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_manager import ProductionAuthManager
import config

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 manual_auth.py <request_token>")
        print("\nSteps:")
        print("1. Go to: https://kite.trade/connect/login?api_key=" + config.API_KEY)
        print("2. Login and authorize")
        print("3. Copy request_token from redirect URL")
        print("4. Run this script with the token")
        sys.exit(1)
    
    request_token = sys.argv[1]
    
    auth_manager = ProductionAuthManager(
        api_key=config.API_KEY,
        api_secret=config.API_SECRET
    )
    
    print("🔐 Authenticating with request token...")
    
    if auth_manager.authenticate_with_request_token(request_token):
        print("✅ Authentication successful!")
        print("✅ Token saved for production use")
        
        # Test the token
        kite = auth_manager.get_kite_instance()
        if kite:
            profile = kite.profile()
            print(f"✅ Logged in as: {profile['user_name']}")
        
    else:
        print("❌ Authentication failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
