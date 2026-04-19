#!/usr/bin/env python3
"""
Production System Monitor
Monitors trading bot health and sends alerts
"""

import os
import sys
import time
import json
import psutil
import datetime as dt
from pathlib import Path
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deployment.telegram_notifier import send_system_status, send_alert, send_emergency_alert
from deployment.production_logger import log_system_metrics

logger = logging.getLogger('monitor')

class SystemMonitor:
    """Production system monitor"""
    
    def __init__(self):
        self.check_interval = 60  # seconds
        self.alert_interval = 300  # 5 minutes between alerts
        self.last_alert_time = {}
        
        # Thresholds
        self.cpu_threshold = 80  # %
        self.memory_threshold = 85  # %
        self.disk_threshold = 90  # %
        
        # Files to monitor
        self.status_files = {
            "websocket": Path("logs/websocket_status.json"),
            "auth": Path("logs/auth_required.alert"),
            "emergency": Path(".emergency_stop"),
            "risk": Path("logs/risk_state.json")
        }
        
        logger.info("🔍 System monitor initialized")
    
    def check_system_resources(self) -> dict:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get trading bot process info
            bot_process = self.find_trading_bot_process()
            
            metrics = {
                "timestamp": dt.datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "bot_process": bot_process
            }
            
            # Check thresholds
            alerts = []
            if cpu_percent > self.cpu_threshold:
                alerts.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > self.memory_threshold:
                alerts.append(f"High memory usage: {memory.percent:.1f}%")
            
            if disk.percent > self.disk_threshold:
                alerts.append(f"Low disk space: {disk.percent:.1f}% used")
            
            metrics["alerts"] = alerts
            return metrics
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {"error": str(e)}
    
    def find_trading_bot_process(self) -> dict:
        """Find trading bot process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'main.py' in cmdline and 'trading_bot' in cmdline:
                        return {
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cpu_percent": proc.info['cpu_percent'],
                            "memory_percent": proc.info['memory_percent'],
                            "status": "running"
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {"status": "not_found"}
            
        except Exception as e:
            logger.error(f"Error finding bot process: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_websocket_status(self) -> dict:
        """Check WebSocket connection status"""
        try:
            ws_file = self.status_files["websocket"]
            if not ws_file.exists():
                return {"status": "no_status_file"}
            
            with open(ws_file, 'r') as f:
                ws_status = json.load(f)
            
            # Check if status is recent (within 2 minutes)
            last_update = dt.datetime.fromisoformat(ws_status.get("last_update", "1970-01-01"))
            time_diff = (dt.datetime.now() - last_update).total_seconds()
            
            if time_diff > 120:  # 2 minutes
                ws_status["stale"] = True
                ws_status["stale_seconds"] = time_diff
            
            return ws_status
            
        except Exception as e:
            logger.error(f"Error checking WebSocket status: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_authentication_status(self) -> dict:
        """Check authentication status"""
        try:
            auth_alert_file = self.status_files["auth"]
            
            if auth_alert_file.exists():
                # Authentication required
                stat = auth_alert_file.stat()
                created_time = dt.datetime.fromtimestamp(stat.st_mtime)
                
                return {
                    "status": "auth_required",
                    "alert_time": created_time.isoformat(),
                    "hours_since": (dt.datetime.now() - created_time).total_seconds() / 3600
                }
            else:
                return {"status": "ok"}
                
        except Exception as e:
            logger.error(f"Error checking auth status: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_emergency_stop(self) -> dict:
        """Check emergency stop status"""
        try:
            emergency_file = self.status_files["emergency"]
            
            if emergency_file.exists():
                with open(emergency_file, 'r') as f:
                    content = f.read()
                
                return {
                    "status": "active",
                    "content": content.strip()
                }
            else:
                return {"status": "inactive"}
                
        except Exception as e:
            logger.error(f"Error checking emergency stop: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_risk_status(self) -> dict:
        """Check risk management status"""
        try:
            risk_file = self.status_files["risk"]
            
            if not risk_file.exists():
                return {"status": "no_risk_file"}
            
            with open(risk_file, 'r') as f:
                risk_data = json.load(f)
            
            # Check if it's today's data
            today = dt.date.today().isoformat()
            if risk_data.get("date") != today:
                return {"status": "stale_data", "date": risk_data.get("date")}
            
            return {
                "status": "ok",
                "daily_pnl": risk_data.get("daily_pnl", 0),
                "trade_count": risk_data.get("trade_count", 0),
                "consecutive_losses": risk_data.get("consecutive_losses", 0)
            }
            
        except Exception as e:
            logger.error(f"Error checking risk status: {e}")
            return {"status": "error", "error": str(e)}
    
    def should_send_alert(self, alert_type: str) -> bool:
        """Check if we should send alert (rate limiting)"""
        now = time.time()
        last_alert = self.last_alert_time.get(alert_type, 0)
        
        if now - last_alert > self.alert_interval:
            self.last_alert_time[alert_type] = now
            return True
        
        return False
    
    def run_health_check(self) -> dict:
        """Run complete health check"""
        logger.info("🔍 Running health check...")
        
        health_status = {
            "timestamp": dt.datetime.now().isoformat(),
            "system": self.check_system_resources(),
            "websocket": self.check_websocket_status(),
            "authentication": self.check_authentication_status(),
            "emergency_stop": self.check_emergency_stop(),
            "risk": self.check_risk_status()
        }
        
        # Analyze overall health
        issues = []
        
        # System resource issues
        if "alerts" in health_status["system"]:
            issues.extend(health_status["system"]["alerts"])
        
        # Bot process issues
        bot_process = health_status["system"].get("bot_process", {})
        if bot_process.get("status") == "not_found":
            issues.append("Trading bot process not running")
        
        # WebSocket issues
        ws_status = health_status["websocket"]
        if not ws_status.get("connected", False):
            issues.append("WebSocket not connected")
        elif ws_status.get("stale", False):
            issues.append(f"WebSocket status stale ({ws_status.get('stale_seconds', 0):.0f}s)")
        
        # Authentication issues
        auth_status = health_status["authentication"]
        if auth_status.get("status") == "auth_required":
            issues.append("Authentication required")
        
        # Emergency stop
        emergency_status = health_status["emergency_stop"]
        if emergency_status.get("status") == "active":
            issues.append("Emergency stop is active")
        
        health_status["issues"] = issues
        health_status["overall_status"] = "healthy" if not issues else "issues_detected"
        
        return health_status
    
    def send_health_alerts(self, health_status: dict):
        """Send alerts based on health status"""
        issues = health_status.get("issues", [])
        
        if not issues:
            return
        
        # Critical issues (send immediately)
        critical_issues = [
            issue for issue in issues 
            if any(keyword in issue.lower() for keyword in 
                  ["emergency stop", "not running", "auth required"])
        ]
        
        if critical_issues and self.should_send_alert("critical"):
            send_emergency_alert(f"Critical issues detected:\n" + "\n".join(critical_issues))
        
        # Warning issues (rate limited)
        warning_issues = [issue for issue in issues if issue not in critical_issues]
        
        if warning_issues and self.should_send_alert("warning"):
            send_alert(f"System warnings:\n" + "\n".join(warning_issues), "warning")
    
    def log_health_status(self, health_status: dict):
        """Log health status"""
        # Log system metrics
        if "system" in health_status:
            log_system_metrics(health_status["system"])
        
        # Log overall status
        status = health_status.get("overall_status", "unknown")
        issue_count = len(health_status.get("issues", []))
        
        if status == "healthy":
            logger.info("✅ System healthy")
        else:
            logger.warning(f"⚠️  {issue_count} issues detected: {health_status['issues']}")
    
    def run_monitor_loop(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting system monitor loop")
        
        while True:
            try:
                # Run health check
                health_status = self.run_health_check()
                
                # Log status
                self.log_health_status(health_status)
                
                # Send alerts if needed
                self.send_health_alerts(health_status)
                
                # Send periodic status update (every 30 minutes)
                if int(time.time()) % 1800 == 0:  # Every 30 minutes
                    status_summary = {
                        "websocket_connected": health_status["websocket"].get("connected", False),
                        "auth_valid": health_status["authentication"].get("status") == "ok",
                        "trading_allowed": health_status["emergency_stop"].get("status") == "inactive",
                        "issues_count": len(health_status.get("issues", []))
                    }
                    send_system_status(status_summary)
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(self.check_interval)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/monitor.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create and run monitor
    monitor = SystemMonitor()
    
    # Run single check if argument provided
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        print("🔍 Running single health check...")
        health_status = monitor.run_health_check()
        
        print(f"\n📊 Health Status:")
        print(f"Overall: {health_status['overall_status']}")
        print(f"Issues: {len(health_status['issues'])}")
        
        if health_status['issues']:
            print("Issues found:")
            for issue in health_status['issues']:
                print(f"  - {issue}")
        
        # Print detailed status
        print(f"\n🖥️  System Resources:")
        system = health_status['system']
        print(f"  CPU: {system.get('cpu_percent', 0):.1f}%")
        print(f"  Memory: {system.get('memory_percent', 0):.1f}%")
        print(f"  Disk: {system.get('disk_percent', 0):.1f}%")
        
        print(f"\n📡 WebSocket:")
        ws = health_status['websocket']
        print(f"  Connected: {ws.get('connected', False)}")
        print(f"  Tick Count: {ws.get('tick_count', 0)}")
        
        print(f"\n🔐 Authentication:")
        auth = health_status['authentication']
        print(f"  Status: {auth.get('status', 'unknown')}")
        
    else:
        # Run continuous monitoring
        monitor.run_monitor_loop()
