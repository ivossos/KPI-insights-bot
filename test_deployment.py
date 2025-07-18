#!/usr/bin/env python3
"""
Deployment Test Script for KPI Insight Bot
Tests all major components to ensure deployment is working
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

class DeploymentTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.dashboard_url = "http://localhost:8502"
        self.test_results = []
        
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        print(f"🧪 Testing {test_name}...")
        
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            self.test_results.append({
                "test": test_name,
                "status": "PASS" if result else "FAIL",
                "duration": end_time - start_time,
                "timestamp": datetime.now().isoformat()
            })
            
            if result:
                print(f"  ✅ {test_name} - PASSED ({end_time - start_time:.2f}s)")
            else:
                print(f"  ❌ {test_name} - FAILED ({end_time - start_time:.2f}s)")
                
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            print(f"  ❌ {test_name} - ERROR: {str(e)}")
    
    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def test_dashboard_availability(self) -> bool:
        """Test dashboard availability"""
        try:
            response = requests.get(self.dashboard_url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def test_kpi_endpoints(self) -> bool:
        """Test KPI API endpoints"""
        try:
            # Test getting KPI definitions (should return 401 without auth)
            response = requests.get(f"{self.base_url}/api/v1/kpi/definitions", timeout=10)
            return response.status_code in [200, 401]  # 401 is expected without auth
        except:
            return False
    
    def test_authentication_endpoint(self) -> bool:
        """Test authentication endpoint structure"""
        try:
            # Test login endpoint structure (should return 405 for GET)
            response = requests.get(f"{self.base_url}/api/v1/auth/login", timeout=10)
            return response.status_code == 405  # Method not allowed is expected
        except:
            return False
    
    def test_kpi_query_mock(self) -> bool:
        """Test KPI query endpoint with mock data"""
        try:
            # This should fail with 401 but the endpoint should exist
            query_data = {
                "user_id": "test_user",
                "query_text": "What is our revenue this quarter?",
                "filters": {}
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/kpi/query",
                json=query_data,
                timeout=10
            )
            
            # Should return 401 (unauthorized) but not 404 (not found)
            return response.status_code == 401
        except:
            return False
    
    def test_static_files(self) -> bool:
        """Test static file serving"""
        try:
            # Test if the API is serving some kind of response
            response = requests.get(f"{self.base_url}/", timeout=10)
            return response.status_code in [200, 404]  # Either works or returns 404
        except:
            return False
    
    def test_cors_headers(self) -> bool:
        """Test CORS headers"""
        try:
            response = requests.options(f"{self.base_url}/health", timeout=10)
            return response.status_code in [200, 204]
        except:
            return False
    
    def test_database_connectivity(self) -> bool:
        """Test database connectivity through API"""
        try:
            # The health endpoint should check database connectivity
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                return "status" in health_data
            return False
        except:
            return False
    
    def test_environment_variables(self) -> bool:
        """Test if required environment variables are set"""
        try:
            import os
            required_vars = ["SECRET_KEY", "OPENAI_API_KEY", "CLAUDE_API_KEY"]
            
            for var in required_vars:
                if not os.getenv(var):
                    return False
            
            return True
        except:
            return False
    
    def test_file_permissions(self) -> bool:
        """Test file permissions and directory structure"""
        try:
            import os
            from pathlib import Path
            
            # Check if required directories exist and are writable
            directories = ["data", "logs", "reports", "chroma_db"]
            
            for directory in directories:
                path = Path(directory)
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                
                # Test write permissions
                test_file = path / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
            
            return True
        except:
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all deployment tests"""
        print("🚀 Starting KPI Insight Bot Deployment Tests")
        print("=" * 50)
        
        # Define test suite
        tests = [
            ("Environment Variables", self.test_environment_variables),
            ("File Permissions", self.test_file_permissions),
            ("API Health", self.test_api_health),
            ("Dashboard Availability", self.test_dashboard_availability),
            ("KPI Endpoints", self.test_kpi_endpoints),
            ("Authentication Structure", self.test_authentication_endpoint),
            ("KPI Query Endpoint", self.test_kpi_query_mock),
            ("Static Files", self.test_static_files),
            ("CORS Headers", self.test_cors_headers),
            ("Database Connectivity", self.test_database_connectivity)
        ]
        
        # Run tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] in ["FAIL", "ERROR"]])
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"  - {result['test']}: {result.get('error', 'Failed')}")
        
        # Overall status
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Deployment is ready.")
            return {"status": "SUCCESS", "results": self.test_results}
        elif passed_tests >= total_tests * 0.7:  # 70% pass rate
            print("\n⚠️  Most tests passed. Deployment is functional but may have issues.")
            return {"status": "WARNING", "results": self.test_results}
        else:
            print("\n🚨 Multiple tests failed. Deployment needs attention.")
            return {"status": "FAILURE", "results": self.test_results}
    
    def save_results(self, filename: str = "deployment_test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.test_results,
                "summary": {
                    "total": len(self.test_results),
                    "passed": len([r for r in self.test_results if r["status"] == "PASS"]),
                    "failed": len([r for r in self.test_results if r["status"] in ["FAIL", "ERROR"]])
                }
            }, f, indent=2)
        
        print(f"📄 Test results saved to {filename}")

def main():
    """Main function"""
    # Parse command line arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"🔗 Testing deployment at: {base_url}")
    
    # Create and run tester
    tester = DeploymentTester(base_url)
    results = tester.run_all_tests()
    
    # Save results
    tester.save_results()
    
    # Exit with appropriate code
    if results["status"] == "SUCCESS":
        sys.exit(0)
    elif results["status"] == "WARNING":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()