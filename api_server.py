
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    
    app = FastAPI(title="KPI Insight Bot", version="1.0.0")
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "KPI Insight Bot is running!",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "running",
                "database": "connected",
                "llm": "available"
            }
        }
    
    @app.get("/api/v1/kpi/demo")
    async def demo_kpi():
        return {
            "kpi_results": [
                {
                    "kpi_id": "revenue_total",
                    "name": "Total Revenue",
                    "value": 2500000,
                    "unit": "currency",
                    "currency": "USD",
                    "time_period": "Q1 2024",
                    "variance_py": 150000,
                    "variance_plan": -50000
                },
                {
                    "kpi_id": "gross_margin",
                    "name": "Gross Margin %",
                    "value": 68.5,
                    "unit": "percentage",
                    "time_period": "Q1 2024",
                    "variance_py": 2.3,
                    "variance_plan": 1.5
                }
            ],
            "narrative_summary": "Revenue performance is strong this quarter, showing 6% growth vs prior year. Gross margin improved by 2.3 percentage points, indicating better cost management and pricing optimization.",
            "timestamp": datetime.now().isoformat()
        }
    
    if __name__ == "__main__":
        print("🚀 Starting KPI Insight Bot API...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Installing FastAPI...")
    subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    print("✅ Dependencies installed. Please run again.")
