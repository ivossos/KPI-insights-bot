# IA Fiscal Capivari - Complete Deployment Guide

## 🎉 Complete System Ready!

The complete IA Fiscal Capivari system is now ready for deployment with multiple running options:

## 🚀 Quick Start Options

### Option 1: Minimal Complete System (Recommended for Replit)
```bash
python3 run_minimal_complete.py
```

### Option 2: Simple API Only
```bash
python3 simple_api.py
```

### Option 3: Simple Dashboard Only (requires Streamlit)
```bash
streamlit run simple_dashboard.py
```

### Option 4: Full System (requires all dependencies)
```bash
python3 run_complete_app.py
```

## 📊 What's Included

### ✅ Working Components:
1. **Simple API Server** (`simple_api.py`)
   - HTTP server with JSON responses
   - Endpoints: `/`, `/health`, `/info`, `/alerts`, `/webhook/ingestion`
   - No external dependencies required
   - CORS enabled for frontend integration

2. **Interactive Dashboard** (`simple_dashboard.py`)
   - Streamlit-based web interface
   - Municipal spending monitoring
   - Alert visualization
   - Real-time API integration
   - Portuguese interface

3. **Complete Launchers**:
   - `run_minimal_complete.py` - Starts both API and dashboard
   - `run_complete_app.py` - Full system with fallbacks
   - `run_simple_complete.py` - Alternative simple launcher

### 📁 Directory Structure Created:
```
ia-fiscal-capivari/
├── data/
│   ├── raw/
│   ├── processed/
│   └── alerts/
├── logs/
├── reports/
└── src/ (full system components)
```

## 🌐 URLs After Starting

- **API Server**: http://localhost:8000
- **Dashboard**: http://localhost:8501

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/info` | System information |
| GET | `/alerts` | Get current alerts |
| POST | `/webhook/ingestion` | Data ingestion webhook |

## 🔧 For Replit Deployment

1. Upload all files to Replit
2. Set the run command to: `python3 run_minimal_complete.py`
3. The system will automatically:
   - Create required directories
   - Start API server on port 8000
   - Start dashboard on port 8501
   - Handle Replit-specific paths

## 📱 Features Demonstrated

### Dashboard Features:
- 📊 Main metrics display
- 🚨 Real-time alerts from API
- 📈 Spending analysis charts
- 👥 Supplier distribution
- ⚙️ Settings panel
- 🔍 Alert filtering and search

### API Features:
- 🔄 RESTful endpoints
- 📊 JSON responses
- 🚨 Alert management
- 📥 Webhook for data ingestion
- 💾 Health monitoring

## 🎯 Current Status

✅ **WORKING**: Complete minimal system with API and dashboard
✅ **TESTED**: API endpoints respond correctly
✅ **READY**: For Replit deployment
✅ **COMPLETE**: Core functionality implemented

## 📞 Usage Examples

### Test API:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/alerts
```

### Send webhook data:
```bash
curl -X POST http://localhost:8000/webhook/ingestion \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": "test123", "data": "sample"}'
```

The system is now **complete and ready** for deployment! 🚀