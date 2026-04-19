#!/usr/bin/env python3
"""
Production WebSocket Manager
Robust WebSocket handling with auto-reconnection and error recovery
"""

import time
import threading
import logging
from typing import Callable, List, Dict, Any
import json
from pathlib import Path
import datetime as dt

logger = logging.getLogger(__name__)

class ProductionWebSocketManager:
    """Production-grade WebSocket manager with reliability features"""
    
    def __init__(self, kite, tokens: List[int], mode="ltp"):
        self.kite = kite
        self.tokens = tokens
        self.mode = mode
        
        # Connection state
        self.is_connected = False
        self.connection_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # seconds
        
        # Callbacks
        self.on_tick_callback = None
        self.on_connect_callback = None
        self.on_disconnect_callback = None
        self.on_error_callback = None
        
        # Monitoring
        self.last_tick_time = None
        self.tick_count = 0
        self.connection_start_time = None
        
        # Health check
        self.health_check_interval = 30  # seconds
        self.max_tick_gap = 60  # seconds without ticks before reconnect
        
        # Status file for monitoring
        self.status_file = Path("logs/websocket_status.json")
        
    def set_callbacks(self, on_tick: Callable = None, on_connect: Callable = None,
                     on_disconnect: Callable = None, on_error: Callable = None):
        """Set callback functions"""
        self.on_tick_callback = on_tick
        self.on_connect_callback = on_connect
        self.on_disconnect_callback = on_disconnect
        self.on_error_callback = on_error
    
    def on_ticks(self, ws, ticks):
        """Handle incoming ticks"""
        try:
            self.last_tick_time = dt.datetime.now()
            self.tick_count += len(ticks)
            
            # Update status
            self.update_status()
            
            # Call user callback
            if self.on_tick_callback:
                self.on_tick_callback(ticks)
                
            # Log tick info (reduced frequency)
            if self.tick_count % 100 == 0:
                logger.debug(f"Processed {self.tick_count} ticks")
                
        except Exception as e:
            logger.error(f"Error processing ticks: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    def on_connect(self, ws, response):
        """Handle WebSocket connection"""
        try:
            self.is_connected = True
            self.connection_attempts = 0
            self.connection_start_time = dt.datetime.now()
            self.tick_count = 0
            
            logger.info("✅ WebSocket connected successfully")
            
            # Subscribe to tokens
            ws.subscribe(self.tokens)
            ws.set_mode(ws.MODE_LTP, self.tokens)  # Use LTP mode for efficiency
            
            logger.info(f"📡 Subscribed to {len(self.tokens)} instruments in {self.mode} mode")
            
            # Update status
            self.update_status()
            
            # Call user callback
            if self.on_connect_callback:
                self.on_connect_callback(response)
                
        except Exception as e:
            logger.error(f"Error in on_connect: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    def on_disconnect(self, ws, code, reason):
        """Handle WebSocket disconnection"""
        try:
            self.is_connected = False
            
            logger.warning(f"❌ WebSocket disconnected: {code} - {reason}")
            
            # Update status
            self.update_status()
            
            # Call user callback
            if self.on_disconnect_callback:
                self.on_disconnect_callback(code, reason)
            
            # Attempt reconnection
            self.schedule_reconnect()
            
        except Exception as e:
            logger.error(f"Error in on_disconnect: {e}")
    
    def on_error(self, ws, code, reason):
        """Handle WebSocket errors"""
        try:
            logger.error(f"❌ WebSocket error: {code} - {reason}")
            
            # Update status
            self.update_status(error=f"{code}: {reason}")
            
            # Call user callback
            if self.on_error_callback:
                self.on_error_callback(Exception(f"{code}: {reason}"))
            
            # Attempt reconnection on certain errors
            if code in [1006, 1011, 1012]:  # Connection errors
                self.schedule_reconnect()
                
        except Exception as e:
            logger.error(f"Error in on_error handler: {e}")
    
    def schedule_reconnect(self):
        """Schedule reconnection attempt"""
        if self.connection_attempts >= self.max_reconnect_attempts:
            logger.critical("❌ Max reconnection attempts reached. Manual intervention required.")
            self.create_alert_file("Max reconnection attempts reached")
            return
        
        self.connection_attempts += 1
        delay = min(self.reconnect_delay * self.connection_attempts, 60)  # Max 60 seconds
        
        logger.info(f"🔄 Scheduling reconnection attempt {self.connection_attempts} in {delay} seconds")
        
        threading.Timer(delay, self.reconnect).start()
    
    def reconnect(self):
        """Attempt to reconnect WebSocket"""
        try:
            logger.info(f"🔄 Reconnection attempt {self.connection_attempts}")
            
            # Stop existing connection
            if hasattr(self, 'kws') and self.kws:
                try:
                    self.kws.close()
                except:
                    pass
            
            # Start new connection
            self.start()
            
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            self.schedule_reconnect()
    
    def start(self):
        """Start WebSocket connection"""
        try:
            from kiteconnect import KiteTicker
            
            # Create KiteTicker instance
            self.kws = KiteTicker(self.kite.api_key, self.kite.access_token)
            
            # Set callbacks
            self.kws.on_ticks = self.on_ticks
            self.kws.on_connect = self.on_connect
            self.kws.on_close = self.on_disconnect
            self.kws.on_error = self.on_error
            
            # Start connection
            logger.info("🚀 Starting WebSocket connection...")
            self.kws.connect(threaded=True)
            
            # Start health check
            self.start_health_check()
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket: {e}")
            self.schedule_reconnect()
    
    def stop(self):
        """Stop WebSocket connection"""
        try:
            self.is_connected = False
            
            if hasattr(self, 'kws') and self.kws:
                self.kws.close()
                logger.info("🛑 WebSocket connection stopped")
            
            # Update status
            self.update_status()
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket: {e}")
    
    def start_health_check(self):
        """Start health monitoring"""
        def health_check():
            while True:
                try:
                    time.sleep(self.health_check_interval)
                    
                    if not self.is_connected:
                        continue
                    
                    # Check if we're receiving ticks
                    if self.last_tick_time:
                        time_since_last_tick = (dt.datetime.now() - self.last_tick_time).total_seconds()
                        
                        if time_since_last_tick > self.max_tick_gap:
                            logger.warning(f"⚠️  No ticks received for {time_since_last_tick:.0f} seconds")
                            self.reconnect()
                    
                    # Update status
                    self.update_status()
                    
                except Exception as e:
                    logger.error(f"Health check error: {e}")
        
        health_thread = threading.Thread(target=health_check, daemon=True)
        health_thread.start()
    
    def update_status(self, error: str = None):
        """Update WebSocket status file"""
        try:
            status = {
                "connected": self.is_connected,
                "connection_attempts": self.connection_attempts,
                "tick_count": self.tick_count,
                "last_tick_time": self.last_tick_time.isoformat() if self.last_tick_time else None,
                "connection_start_time": self.connection_start_time.isoformat() if self.connection_start_time else None,
                "subscribed_tokens": len(self.tokens),
                "mode": self.mode,
                "last_update": dt.datetime.now().isoformat()
            }
            
            if error:
                status["last_error"] = error
            
            # Ensure logs directory exists
            self.status_file.parent.mkdir(exist_ok=True)
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def create_alert_file(self, message: str):
        """Create alert file for monitoring"""
        try:
            alert_file = Path("logs/websocket_alert.txt")
            with open(alert_file, 'w') as f:
                f.write(f"WebSocket Alert: {message}\n")
                f.write(f"Time: {dt.datetime.now()}\n")
                f.write(f"Connection attempts: {self.connection_attempts}\n")
        except Exception as e:
            logger.error(f"Error creating alert file: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current WebSocket status"""
        return {
            "connected": self.is_connected,
            "connection_attempts": self.connection_attempts,
            "tick_count": self.tick_count,
            "last_tick_time": self.last_tick_time,
            "connection_start_time": self.connection_start_time,
            "uptime_seconds": (dt.datetime.now() - self.connection_start_time).total_seconds() 
                            if self.connection_start_time else 0
        }


class ProductionWebSocketFactory:
    """Factory for creating production WebSocket instances"""
    
    @staticmethod
    def create_websocket(kite, symbols: List[str]) -> ProductionWebSocketManager:
        """Create WebSocket for given symbols"""
        
        # Map symbols to tokens (simplified - you should have proper mapping)
        token_map = {
            "NIFTY": 256265,
            "BANKNIFTY": 260105
        }
        
        tokens = [token_map.get(symbol) for symbol in symbols if symbol in token_map]
        tokens = [t for t in tokens if t is not None]  # Remove None values
        
        if not tokens:
            raise ValueError(f"No valid tokens found for symbols: {symbols}")
        
        ws_manager = ProductionWebSocketManager(kite, tokens, mode="ltp")
        
        logger.info(f"Created WebSocket for {len(tokens)} tokens: {tokens}")
        
        return ws_manager


if __name__ == "__main__":
    # Test WebSocket manager
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from deployment.auth_manager import get_production_kite
    
    # Get authenticated kite instance
    kite = get_production_kite()
    if not kite:
        print("❌ Authentication failed")
        sys.exit(1)
    
    # Create WebSocket
    ws_manager = ProductionWebSocketFactory.create_websocket(kite, ["NIFTY", "BANKNIFTY"])
    
    # Set callbacks
    def on_tick(ticks):
        print(f"📊 Received {len(ticks)} ticks")
        for tick in ticks[:2]:  # Show first 2 ticks
            print(f"   {tick['instrument_token']}: ₹{tick['last_price']}")
    
    def on_connect(response):
        print("✅ WebSocket connected")
    
    def on_disconnect(code, reason):
        print(f"❌ WebSocket disconnected: {code} - {reason}")
    
    ws_manager.set_callbacks(
        on_tick=on_tick,
        on_connect=on_connect,
        on_disconnect=on_disconnect
    )
    
    # Start WebSocket
    print("🚀 Starting WebSocket test...")
    ws_manager.start()
    
    try:
        # Keep running
        while True:
            time.sleep(10)
            status = ws_manager.get_status()
            print(f"Status: Connected={status['connected']}, Ticks={status['tick_count']}")
    except KeyboardInterrupt:
        print("\n🛑 Stopping WebSocket...")
        ws_manager.stop()
