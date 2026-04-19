#!/usr/bin/env python3
"""
Telegram Notification System
Send alerts for trades, errors, and system status
"""

import os
import json
import logging
import datetime as dt
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import telegram
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logging.warning("python-telegram-bot not installed. Telegram notifications disabled.")

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Telegram notification system for trading bot"""
    
    def __init__(self, config_file="deployment/telegram_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.bot = None
        
        if TELEGRAM_AVAILABLE and self.config.get("enabled", False):
            self.initialize_bot()
    
    def load_config(self) -> Dict[str, Any]:
        """Load Telegram configuration"""
        default_config = {
            "enabled": False,
            "bot_token": "",
            "chat_id": "",
            "alerts": {
                "trades": True,
                "errors": True,
                "daily_summary": True,
                "system_status": True,
                "emergency": True
            },
            "quiet_hours": {
                "enabled": False,
                "start": "22:00",
                "end": "08:00"
            }
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                merged_config = default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                # Create default config
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading Telegram config: {e}")
            return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save Telegram configuration"""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving Telegram config: {e}")
    
    def initialize_bot(self):
        """Initialize Telegram bot"""
        try:
            if not self.config.get("bot_token") or not self.config.get("chat_id"):
                logger.warning("Telegram bot token or chat ID not configured")
                return
            
            self.bot = Bot(token=self.config["bot_token"])
            
            # Test connection
            bot_info = self.bot.get_me()
            logger.info(f"✅ Telegram bot initialized: @{bot_info.username}")
            
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")
            self.bot = None
    
    def is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours"""
        if not self.config["quiet_hours"]["enabled"]:
            return False
        
        try:
            now = dt.datetime.now().time()
            start_time = dt.datetime.strptime(self.config["quiet_hours"]["start"], "%H:%M").time()
            end_time = dt.datetime.strptime(self.config["quiet_hours"]["end"], "%H:%M").time()
            
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:  # Overnight quiet hours
                return now >= start_time or now <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
    
    def send_message(self, message: str, alert_type: str = "info", 
                    force: bool = False) -> bool:
        """Send message to Telegram"""
        
        if not TELEGRAM_AVAILABLE or not self.bot:
            logger.debug(f"Telegram not available: {message}")
            return False
        
        if not self.config.get("enabled", False):
            return False
        
        # Check if this alert type is enabled
        if not force and not self.config["alerts"].get(alert_type, True):
            return False
        
        # Check quiet hours (except for emergency alerts)
        if not force and alert_type != "emergency" and self.is_quiet_hours():
            logger.debug(f"Skipping alert during quiet hours: {message}")
            return False
        
        try:
            # Add emoji based on alert type
            emoji_map = {
                "trade": "💰",
                "error": "❌",
                "emergency": "🚨",
                "success": "✅",
                "warning": "⚠️",
                "info": "ℹ️",
                "daily_summary": "📊",
                "system_status": "🖥️"
            }
            
            emoji = emoji_map.get(alert_type, "📢")
            formatted_message = f"{emoji} {message}"
            
            # Add timestamp
            timestamp = dt.datetime.now().strftime("%H:%M:%S")
            formatted_message += f"\n\n🕐 {timestamp}"
            
            # Send message
            self.bot.send_message(
                chat_id=self.config["chat_id"],
                text=formatted_message,
                parse_mode='HTML'
            )
            
            logger.debug(f"Telegram message sent: {alert_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_trade_alert(self, trade_data: Dict[str, Any]):
        """Send trade execution alert"""
        try:
            symbol = trade_data.get("symbol", "Unknown")
            side = trade_data.get("side", "Unknown")
            quantity = trade_data.get("quantity", 0)
            price = trade_data.get("price", 0)
            pnl = trade_data.get("pnl")
            
            message = f"<b>Trade Executed</b>\n"
            message += f"Symbol: {symbol}\n"
            message += f"Side: {side}\n"
            message += f"Quantity: {quantity}\n"
            message += f"Price: ₹{price:.2f}"
            
            if pnl is not None:
                pnl_emoji = "📈" if pnl >= 0 else "📉"
                message += f"\n{pnl_emoji} PnL: ₹{pnl:.2f}"
            
            self.send_message(message, "trade")
            
        except Exception as e:
            logger.error(f"Error sending trade alert: {e}")
    
    def send_error_alert(self, error_message: str, error_type: str = "Error"):
        """Send error alert"""
        message = f"<b>{error_type}</b>\n{error_message}"
        self.send_message(message, "error")
    
    def send_daily_summary(self, summary_data: Dict[str, Any]):
        """Send daily trading summary"""
        try:
            date = summary_data.get("date", dt.date.today().isoformat())
            pnl = summary_data.get("daily_pnl", 0)
            trades = summary_data.get("trade_count", 0)
            
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            
            message = f"<b>Daily Summary - {date}</b>\n"
            message += f"{pnl_emoji} P&L: ₹{pnl:.2f}\n"
            message += f"📊 Trades: {trades}\n"
            
            if "max_drawdown" in summary_data:
                message += f"📉 Max Drawdown: ₹{summary_data['max_drawdown']:.2f}\n"
            
            if "consecutive_losses" in summary_data:
                message += f"🔄 Consecutive Losses: {summary_data['consecutive_losses']}"
            
            self.send_message(message, "daily_summary")
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def send_system_status(self, status_data: Dict[str, Any]):
        """Send system status alert"""
        try:
            message = "<b>System Status</b>\n"
            
            # WebSocket status
            ws_connected = status_data.get("websocket_connected", False)
            ws_emoji = "✅" if ws_connected else "❌"
            message += f"{ws_emoji} WebSocket: {'Connected' if ws_connected else 'Disconnected'}\n"
            
            # Authentication status
            auth_valid = status_data.get("auth_valid", False)
            auth_emoji = "✅" if auth_valid else "❌"
            message += f"{auth_emoji} Authentication: {'Valid' if auth_valid else 'Invalid'}\n"
            
            # Trading status
            trading_allowed = status_data.get("trading_allowed", False)
            trading_emoji = "✅" if trading_allowed else "⏸️"
            message += f"{trading_emoji} Trading: {'Allowed' if trading_allowed else 'Stopped'}"
            
            self.send_message(message, "system_status")
            
        except Exception as e:
            logger.error(f"Error sending system status: {e}")
    
    def send_emergency_alert(self, message: str):
        """Send emergency alert (always sent, ignores quiet hours)"""
        emergency_message = f"<b>🚨 EMERGENCY ALERT 🚨</b>\n{message}"
        self.send_message(emergency_message, "emergency", force=True)


# Global notifier instance
notifier = TelegramNotifier()


def send_trade_alert(trade_data: Dict[str, Any]):
    """Quick function to send trade alert"""
    notifier.send_trade_alert(trade_data)


def send_error_alert(error_message: str, error_type: str = "Error"):
    """Quick function to send error alert"""
    notifier.send_error_alert(error_message, error_type)


def send_daily_summary(summary_data: Dict[str, Any]):
    """Quick function to send daily summary"""
    notifier.send_daily_summary(summary_data)


def send_system_status(status_data: Dict[str, Any]):
    """Quick function to send system status"""
    notifier.send_system_status(status_data)


def send_alert(message: str, alert_type: str = "info"):
    """Quick function to send general alert"""
    notifier.send_message(message, alert_type)


def send_emergency_alert(message: str):
    """Quick function to send emergency alert"""
    notifier.send_emergency_alert(message)


if __name__ == "__main__":
    # Test Telegram notifier
    print("📱 Testing Telegram Notifier")
    
    if not TELEGRAM_AVAILABLE:
        print("❌ python-telegram-bot not installed")
        print("Install with: pip install python-telegram-bot")
        exit(1)
    
    # Test configuration
    config = notifier.config
    print(f"Enabled: {config.get('enabled', False)}")
    print(f"Bot Token: {'Set' if config.get('bot_token') else 'Not set'}")
    print(f"Chat ID: {'Set' if config.get('chat_id') else 'Not set'}")
    
    if config.get("enabled") and config.get("bot_token") and config.get("chat_id"):
        # Send test message
        success = send_alert("🧪 Test message from trading bot", "info")
        print(f"Test message sent: {success}")
        
        # Send test trade alert
        test_trade = {
            "symbol": "NIFTY2642124350CE",
            "side": "BUY",
            "quantity": 50,
            "price": 100.50,
            "pnl": 250.75
        }
        send_trade_alert(test_trade)
        
        # Send test system status
        test_status = {
            "websocket_connected": True,
            "auth_valid": True,
            "trading_allowed": True
        }
        send_system_status(test_status)
        
    else:
        print("❌ Telegram not properly configured")
        print("Edit deployment/telegram_config.json to configure")
