#!/usr/bin/env python3
"""
Health Check Script for KPI Insight Bot
Monitors system health and provides status information
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

class HealthChecker:
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.dashboard_url = "http://localhost:8502"
        self.timeout = 10
        
    def check_api_health(self) -> Dict[str, Any]:
        """Check API health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=self.timeout)
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                }
                
        except requests.RequestException as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": None
            }
    
    def check_dashboard_health(self) -> Dict[str, Any]:
        """Check dashboard availability"""
        try:
            response = requests.get(self.dashboard_url, timeout=self.timeout)
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                }
                
        except requests.RequestException as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": None
            }
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity through API"""
        try:
            # Try to access KPI definitions endpoint
            response = requests.get(f"{self.api_url}/api/v1/kpi/definitions", timeout=self.timeout)
            
            if response.status_code in [200, 401]:  # 401 is expected without auth
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                }
                
        except requests.RequestException as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": None
            }
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        print(f"🔍 Running health check at {datetime.now()}")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {}
        }
        
        # Check API
        print("  Checking API...")
        api_health = self.check_api_health()
        results["services"]["api"] = api_health
        
        if api_health["status"] != "healthy":
            results["overall_status"] = "unhealthy"
            print(f"  ❌ API: {api_health['error']}")
        else:
            print(f"  ✅ API: {api_health['response_time']:.2f}s")
        
        # Check Dashboard
        print("  Checking Dashboard...")
        dashboard_health = self.check_dashboard_health()
        results["services"]["dashboard"] = dashboard_health
        
        if dashboard_health["status"] != "healthy":
            results["overall_status"] = "unhealthy"
            print(f"  ❌ Dashboard: {dashboard_health['error']}")
        else:
            print(f"  ✅ Dashboard: {dashboard_health['response_time']:.2f}s")
        
        # Check Database
        print("  Checking Database...")
        db_health = self.check_database_health()
        results["services"]["database"] = db_health
        
        if db_health["status"] != "healthy":
            results["overall_status"] = "unhealthy"
            print(f"  ❌ Database: {db_health['error']}")
        else:
            print(f"  ✅ Database: {db_health['response_time']:.2f}s")
        
        # Overall status
        if results["overall_status"] == "healthy":
            print("🟢 Overall Status: HEALTHY")
        else:
            print("🔴 Overall Status: UNHEALTHY")
        
        return results
    
    def monitor_continuously(self, interval: int = 30):
        """Monitor health continuously"""
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        
        while True:
            try:
                results = self.run_health_check()
                
                # Save results to file
                with open("logs/health_check.json", "w") as f:
                    json.dump(results, f, indent=2)
                
                print(f"💾 Results saved to logs/health_check.json")
                print("-" * 50)
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(interval)

def main():
    """Main function"""
    checker = HealthChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        checker.monitor_continuously(interval)
    else:
        results = checker.run_health_check()
        
        # Exit with error code if unhealthy
        if results["overall_status"] != "healthy":
            sys.exit(1)

if __name__ == "__main__":
    main()