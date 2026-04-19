#!/usr/bin/env python3
"""
Enhanced Authentication Manager for Production Deployment
Handles token refresh, validation, and automatic re-authentication
"""

import os
import json
import datetime as dt
from pathlib import Path
import time
import logging
from kiteconnect import KiteConnect

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionAuthManager:
    """Enhanced authentication manager for production deployment"""
    
    def __init__(self, api_key, api_secret, token_file="token.json"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.token_file = Path(token_file)
        self.kite = None
        self.access_token = None
        self.token_expiry = None
        
    def load_token(self):
        """Load existing token from file"""
        try:
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                
                self.access_token = token_data.get('access_token')
                expiry_str = token_data.get('expiry')
                
                if expiry_str:
                    self.token_expiry = dt.datetime.fromisoformat(expiry_str)
                
                logger.info(f"Token loaded. Expires: {self.token_expiry}")
                return True
                
        except Exception as e:
            logger.error(f"Error loading token: {e}")
        
        return False
    
    def save_token(self, access_token):
        """Save token to file with expiry"""
        try:
            # Zerodha tokens expire at 6 AM next day
            now = dt.datetime.now()
            if now.hour >= 6:
                expiry = now.replace(hour=6, minute=0, second=0, microsecond=0) + dt.timedelta(days=1)
            else:
                expiry = now.replace(hour=6, minute=0, second=0, microsecond=0)
            
            token_data = {
                'access_token': access_token,
                'expiry': expiry.isoformat(),
                'created_at': now.isoformat()
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            self.access_token = access_token
            self.token_expiry = expiry
            
            logger.info(f"Token saved. Expires: {expiry}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving token: {e}")
            return False
    
    def is_token_valid(self):
        """Check if current token is valid"""
        if not self.access_token or not self.token_expiry:
            return False
        
        # Check if token has expired (with 30 minute buffer)
        buffer_time = dt.timedelta(minutes=30)
        if dt.datetime.now() >= (self.token_expiry - buffer_time):
            logger.warning("Token expired or expiring soon")
            return False
        
        # Test token with API call
        try:
            if not self.kite:
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
            
            # Test API call
            profile = self.kite.profile()
            logger.info(f"Token valid for user: {profile.get('user_name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
    
    def get_kite_instance(self):
        """Get authenticated KiteConnect instance"""
        # Try to load existing token
        if not self.access_token:
            self.load_token()
        
        # Validate token
        if self.is_token_valid():
            if not self.kite:
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
            return self.kite
        
        # Token invalid, need manual intervention
        logger.error("Token invalid or expired. Manual authentication required.")
        self.request_manual_auth()
        return None
    
    def request_manual_auth(self):
        """Request manual authentication"""
        logger.critical("MANUAL AUTHENTICATION REQUIRED!")
        logger.critical("Steps to authenticate:")
        logger.critical("1. Go to: https://kite.trade/connect/login?api_key=" + self.api_key)
        logger.critical("2. Login and authorize the app")
        logger.critical("3. Copy the request_token from redirect URL")
        logger.critical("4. Run: python3 deployment/manual_auth.py <request_token>")
        
        # Create alert file for monitoring
        alert_file = Path("logs/auth_required.alert")
        with open(alert_file, 'w') as f:
            f.write(f"Authentication required at {dt.datetime.now()}\n")
    
    def authenticate_with_request_token(self, request_token):
        """Authenticate using request token"""
        try:
            kite = KiteConnect(api_key=self.api_key)
            data = kite.generate_session(request_token, api_secret=self.api_secret)
            
            access_token = data["access_token"]
            
            if self.save_token(access_token):
                self.kite = kite
                logger.info("Authentication successful!")
                
                # Remove alert file
                alert_file = Path("logs/auth_required.alert")
                if alert_file.exists():
                    alert_file.unlink()
                
                return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
        
        return False
    
    def check_market_hours(self):
        """Check if market is open"""
        now = dt.datetime.now()
        
        # Check if weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False, "Weekend"
        
        # Check market hours (9:15 AM to 3:30 PM)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if now < market_open:
            return False, f"Before market open ({market_open.strftime('%H:%M')})"
        elif now > market_close:
            return False, f"After market close ({market_close.strftime('%H:%M')})"
        else:
            return True, "Market open"
    
    def get_production_kite(self):
        """Main method for production use"""
        # Check market hours first
        is_open, status = self.check_market_hours()
        if not is_open:
            logger.info(f"Market status: {status}")
            return None
        
        # Get authenticated instance
        kite = self.get_kite_instance()
        if kite:
            logger.info("✅ Authentication successful - Ready for trading")
        else:
            logger.error("❌ Authentication failed - Manual intervention required")
        
        return kite


def get_production_kite():
    """Factory function for production KiteConnect instance"""
    import config
    
    auth_manager = ProductionAuthManager(
        api_key=config.API_KEY,
        api_secret=config.API_SECRET
    )
    
    return auth_manager.get_production_kite()


if __name__ == "__main__":
    # Test authentication
    kite = get_production_kite()
    if kite:
        try:
            profile = kite.profile()
            print(f"✅ Authenticated as: {profile['user_name']}")
            print(f"✅ User ID: {profile['user_id']}")
            print(f"✅ Broker: {profile['broker']}")
        except Exception as e:
            print(f"❌ Error testing API: {e}")
    else:
        print("❌ Authentication failed")
