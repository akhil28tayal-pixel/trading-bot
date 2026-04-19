#!/usr/bin/env python3
"""
Interactive Telegram Bot for Trading Bot
Handles commands like /help, /status, /positions, etc.
"""

import time
import os
import sys
import json
import threading
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import requests

class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_TOKEN
        self.chat_id = config.CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.running = True
        
    def send_message(self, message, chat_id=None):
        """Send message to Telegram"""
        try:
            chat_id = chat_id or self.chat_id
            if not chat_id:
                print("No chat_id configured")
                return False
                
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False
    
    def get_updates(self, offset=None):
        """Get updates from Telegram"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {'timeout': 30, 'offset': offset} if offset else {'timeout': 30}
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Telegram get updates error: {e}")
        return None
    
    def handle_command(self, message):
        """Handle incoming commands"""
        chat_id = message['chat']['id']
        text = message.get('text', '').lower()
        
        print(f"Received command: {text} from chat_id: {chat_id}")
        
        # Store chat_id if not configured
        if not self.chat_id and chat_id:
            self.chat_id = chat_id
            print(f"Updated chat_id to: {chat_id}")
        
        if text == '/help':
            response = """<b>Trading Bot Commands:</b>

<b>Basic Commands:</b>
/help - Show this help message
/status - Get bot status
/time - Current server time

<b>Trading Commands:</b>
/positions - Current positions
/pnl - Today's P&L
/orders - Recent orders
/balance - Account balance

<b>Authentication:</b>
/auth - Get Kite login link for authentication
/checktoken - Check token validity

<b>System Commands:</b>
/logs - View recent log entries
/logfiles - List available log files
/restart - Restart bot (admin only)
/stop - Stop bot (admin only)

<b>Note:</b> Some commands require admin privileges."""
            
        elif text == '/status':
            try:
                # Check if main bot is running
                import subprocess
                result = subprocess.run(['pgrep', '-f', 'python.*main.py'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    status = "RUNNING"
                else:
                    status = "STOPPED"
                
                response = f"""<b>Bot Status:</b>

<b>Main Bot:</b> {status}
<b>Telegram Bot:</b> RUNNING
<b>Mode:</b> {config.MODE}
<b>Server Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
<b>Market Hours:</b> 9:15 AM - 3:30 PM (Mon-Fri)"""
            except Exception as e:
                response = f"Error getting status: {e}"
        
        elif text == '/time':
            response = f"<b>Server Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        elif text == '/positions':
            response = "<b>Current Positions:</b>\n\nNo open positions (Paper Trading Mode)"
        
        elif text == '/pnl':
            response = """<b>Today's P&L:</b>

<b>Realized P&L:</b> Rs. 0.00
<b>Unrealized P&L:</b> Rs. 0.00
<b>Total P&L:</b> Rs. 0.00

<i>Paper Trading Mode - No real trades executed</i>"""
        
        elif text == '/orders':
            response = "<b>Recent Orders:</b>\n\nNo recent orders (Paper Trading Mode)"
        
        elif text == '/balance':
            response = f"""<b>Account Balance:</b>

<b>Available Capital:</b> Rs. {config.CAPITAL:,.2f}
<b>Mode:</b> {config.MODE}
<b>Risk per Trade:</b> {config.RISK_PER_TRADE * 100:.1f}%"""
        
        elif text == '/logs':
            try:
                # Get project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                log_files = [
                    os.path.join(project_root, 'logs', 'main.log'),
                    os.path.join(project_root, 'logs', 'telegram_bot.log'),
                    os.path.join(project_root, 'bot.log')
                ]
                
                response = "<b>Recent Logs:</b>\n\n"
                logs_found = False
                
                for log_file in log_files:
                    if os.path.exists(log_file):
                        logs_found = True
                        log_name = os.path.basename(log_file)
                        try:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                last_lines = lines[-5:] if len(lines) >= 5 else lines
                                response += f"\n<b>{log_name}:</b>\n"
                                response += "".join(last_lines)[:500]  # Limit to 500 chars per file
                                response += "\n"
                        except Exception as e:
                            response += f"\n<b>{log_name}:</b> Error reading - {e}\n"
                
                if not logs_found:
                    response += "No log files found. Logs will be created when the bot runs."
                    
            except Exception as e:
                response = f"Error reading logs: {e}"
        
        elif text == '/logfiles':
            try:
                # Get project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                log_locations = [
                    os.path.join(project_root, 'logs'),
                    project_root
                ]
                
                response = "<b>Available Log Files:</b>\n\n"
                files_found = False
                
                for location in log_locations:
                    if os.path.exists(location):
                        for file in os.listdir(location):
                            if file.endswith('.log'):
                                files_found = True
                                file_path = os.path.join(location, file)
                                size = os.path.getsize(file_path)
                                size_kb = size / 1024
                                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                                
                                response += f"📄 <b>{file}</b>\n"
                                response += f"   Size: {size_kb:.1f} KB\n"
                                response += f"   Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                if not files_found:
                    response += "No log files found yet.\n"
                    response += "Logs will be created when the bot runs."
                    
            except Exception as e:
                response = f"Error listing log files: {e}"
        
        elif text == '/auth':
            try:
                # Import fixed auth handler
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                # Trigger direct authentication
                response = """Starting Mobile Authentication...

Please wait while I set up the authentication server...

This will take about 5-10 seconds.

You'll receive authentication instructions shortly!"""
                
                # Send initial message
                self.send_message(response, chat_id)
                
                # Start fixed auth in background
                def start_fixed_auth():
                    try:
                        from mobile_auth_fixed import start_direct_auth
                        start_direct_auth()
                    except Exception as e:
                        self.send_message(f"Authentication Setup Failed\n\n{e}\n\nPlease try again or contact support.", chat_id)
                
                threading.Thread(target=start_fixed_auth, daemon=True).start()
                
                # Don't send another response, the fixed auth will send it
                return
                
            except Exception as e:
                response = f"Error starting authentication: {e}\n\nPlease ensure the bot is running on EC2."
        
        elif text == '/checktoken':
            try:
                # Check token validity
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from telegram_auth_handler import check_token_validity
                
                is_valid, expiry, needs_auth = check_token_validity()
                
                if needs_auth:
                    response = """⚠️ <b>Token Status: EXPIRED</b>

Your Zerodha access token has expired or is missing.

<b>Action Required:</b>
Use /auth command to get authentication link.

<i>Authentication is required before market opens (9:15 AM).</i>"""
                else:
                    if expiry:
                        time_left = expiry - datetime.now()
                        hours_left = time_left.total_seconds() / 3600
                        
                        response = f"""✅ <b>Token Status: VALID</b>

Your Zerodha access token is active.

<b>Token Details:</b>
• Status: Active
• Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}
• Time Left: {hours_left:.1f} hours

<b>Bot is ready to trade!</b>"""
                    else:
                        response = """✅ <b>Token Status: VALID</b>

Your Zerodha access token is active for today.

<b>Bot is ready to trade!</b>"""
                        
            except Exception as e:
                response = f"Error checking token: {e}"
        
        elif text == '/restart':
            response = "Restart command received. Bot will restart in 5 seconds..."
            # Schedule restart in separate thread
            threading.Thread(target=self._restart_bot, daemon=True).start()
        
        elif text == '/stop':
            response = "Stop command received. Bot will stop in 5 seconds..."
            self.running = False
        
        else:
            response = """<b>Unknown command.</b>

Type /help to see available commands."""
        
        self.send_message(response, chat_id)
    
    def _restart_bot(self):
        """Restart the main bot"""
        time.sleep(5)
        try:
            import subprocess
            subprocess.run(['sudo', 'supervisorctl', 'restart', 'trading_bot'], 
                          check=True)
        except Exception as e:
            print(f"Restart error: {e}")
    
    def run(self):
        """Main bot loop"""
        print("Starting interactive Telegram bot...")
        
        if not self.token:
            print("No TELEGRAM_TOKEN configured")
            return
        
        offset = None
        
        while self.running:
            try:
                updates = self.get_updates(offset)
                if updates and updates.get('ok'):
                    for result in updates['result']:
                        # Update offset to mark as processed
                        offset = result['update_id'] + 1
                        
                        # Handle message
                        if 'message' in result:
                            self.handle_command(result['message'])
                
                time.sleep(1)  # Small delay between requests
                
            except KeyboardInterrupt:
                print("Bot stopped by user")
                break
            except Exception as e:
                print(f"Bot error: {e}")
                time.sleep(5)  # Wait before retrying
        
        print("Telegram bot stopped")

if __name__ == "__main__":
    bot = TelegramBot()
    
    # Send startup message
    bot.send_message("Trading Bot Telegram Interface Started!\n\nType /help for commands.")
    
    # Run the bot
    bot.run()
