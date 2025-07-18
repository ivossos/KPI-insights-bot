#!/usr/bin/env python3
"""
Very simple API server for IA Fiscal Capivari
Works with minimal dependencies
"""

import json
import http.server
import socketserver
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class SimpleAPIHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP request handler for the API"""
    
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        if path == '/':
            self._send_json({
                "message": "IA Fiscal Capivari API",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            })
        elif path == '/health':
            self._send_json({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "api": "running",
                    "database": "connected",
                    "monitoring": "active"
                }
            })
        elif path == '/info':
            self._send_json({
                "system": "IA Fiscal Capivari",
                "description": "Municipal spending monitoring with AI",
                "features": [
                    "Automated data collection",
                    "AI-powered anomaly detection", 
                    "Real-time alerts",
                    "Interactive dashboard",
                    "Comprehensive reporting"
                ]
            })
        elif path == '/alerts':
            self._send_json({
                "alerts": [
                    {
                        "id": "alert_001",
                        "type": "overpricing",
                        "description": "Item priced 35% above market average",
                        "risk_score": 8,
                        "created_at": "2024-01-15T08:30:00",
                        "status": "pending"
                    },
                    {
                        "id": "alert_002", 
                        "type": "split_orders",
                        "description": "Potential order splitting detected",
                        "risk_score": 6,
                        "created_at": "2024-01-15T09:15:00",
                        "status": "investigated"
                    }
                ],
                "total": 2,
                "timestamp": datetime.now().isoformat()
            })
        else:
            self._send_error(404, "Not Found")
            
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        
        if path == '/webhook/ingestion':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                print(f"Webhook received: {data}")
                
                self._send_json({
                    "status": "accepted",
                    "message": "Webhook received successfully",
                    "timestamp": datetime.now().isoformat(),
                    "data_id": data.get("dataset_id", "unknown")
                })
            except Exception as e:
                self._send_error(500, f"Webhook processing failed: {str(e)}")
        else:
            self._send_error(404, "Not Found")
            
    def _send_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
        
    def _send_error(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = {
            "error": message,
            "timestamp": datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(error_data).encode())

def run_server(port=8000):
    """Run the simple API server"""
    print(f"🚀 Starting Simple API Server on port {port}")
    print(f"🌐 API available at: http://localhost:{port}")
    print("📋 Endpoints:")
    print("   GET  /         - API info")
    print("   GET  /health   - Health check")
    print("   GET  /info     - System info") 
    print("   GET  /alerts   - Get alerts")
    print("   POST /webhook/ingestion - Webhook")
    print("Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", port), SimpleAPIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    run_server()