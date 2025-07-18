# KPI Insight Bot - Implementation Guide

## Overview

The KPI Insight Bot is a comprehensive conversational assistant that enables finance and operations teams to query key business metrics using natural language. This implementation has been integrated into the existing IA Fiscal Capivari system and provides the full feature set outlined in the PRD.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        KPI Insight Bot                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   Chat Interface│    │   Intent Engine │    │   Metric    │  │
│  │   (Streamlit)   │────│   (NLP + RAG)   │────│   Catalog   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   Auth System   │    │   Oracle EPM    │    │   KPI       │  │
│  │   (JWT + SSO)   │────│   Connector     │────│   Engine    │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   LLM Summary   │    │   Visualizations│    │   Anomaly   │  │
│  │   (GPT/Claude)  │────│   (Plotly)      │────│   Detection │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features Implemented

### ✅ Core Features (Complete)

1. **Authentication & Role-Based Access**
   - JWT-based authentication with email/password
   - Role-based permissions (Admin, Analyst, Viewer)
   - SSO integration ready (Google, Corporate)

2. **Natural Language Query Interface**
   - Intent detection using NLP
   - RAG-powered metric catalog search
   - Query enhancement with LLM

3. **RAG-Enabled Metric Catalog**
   - ChromaDB vector database
   - Semantic search for KPI definitions
   - Centralized metric governance

4. **Oracle EPM/ERP Integration**
   - FCCS (Financial Consolidation and Close)
   - EPBCS (Enterprise Planning and Budgeting)
   - ARCS (Account Reconciliation)
   - Oracle Fusion Financials Cloud

5. **KPI Calculation Engine**
   - Real-time aggregation
   - Variance calculations (PY, Plan, FX-neutral)
   - Caching for performance

6. **LLM Narrative Summarization**
   - GPT-4/Claude integration
   - Context-aware explanations
   - Business insight generation

7. **Interactive Visualizations**
   - Plotly charts with dark theme
   - Drill-down capabilities
   - Dashboard overview

### 🔄 Advanced Features (In Progress)

8. **Alerting & Anomaly Detection**
   - Statistical anomaly detection
   - Machine learning models
   - Threshold-based alerts

9. **Governance Console**
   - KPI definition management
   - Audit trail logging
   - User management

10. **Subscription & Tiered Access**
    - Basic, Advanced, Enterprise tiers
    - Feature gating by subscription

## Installation & Setup

### Prerequisites

```bash
# Python 3.8+
# Node.js 16+ (for any frontend components)
# Oracle EPM access
# OpenAI/Claude API keys
```

### Installation Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create a `.env` file with:
   ```env
   SECRET_KEY=your-secret-key-here
   OPENAI_API_KEY=your-openai-api-key
   CLAUDE_API_KEY=your-claude-api-key
   ORACLE_EPM_HOST=your-epm-host.com
   ORACLE_EPM_USERNAME=your-username
   ORACLE_EPM_PASSWORD=your-password
   ```

3. **Initialize System**
   ```bash
   python run_kpi_bot.py --mode setup
   ```

4. **Start the System**
   ```bash
   # Complete system (API + Dashboard)
   python run_kpi_bot.py --mode complete
   
   # API only
   python run_kpi_bot.py --mode api
   
   # Dashboard only
   python run_kpi_bot.py --mode dashboard
   ```

## Usage Guide

### 1. Login

Access the dashboard at `http://localhost:8502`

Demo credentials:
- Admin: `admin@company.com` / `admin123`
- Analyst: `analyst@company.com` / `analyst123`

### 2. Natural Language Queries

Example queries:
- "What's our revenue variance this quarter?"
- "Show me OPEX performance vs plan"
- "How is our gross margin trending?"
- "What's the cash position by region?"

### 3. Available KPIs

Pre-configured KPIs:
- **Total Revenue**: Sum of all revenue streams
- **Gross Margin %**: Profitability percentage
- **OPEX Variance**: Operating expenses vs plan
- **Cash Position**: Current liquidity

### 4. Visualizations

- **Gauge Charts**: Single KPI performance
- **Bar Charts**: Multiple KPI comparison
- **Variance Charts**: PY, Plan, FX-neutral analysis
- **Trend Analysis**: Historical patterns

## API Reference

### Authentication

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "password123"
}
```

### Query KPIs

```bash
POST /api/v1/kpi/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "user123",
  "query_text": "What's our revenue this quarter?",
  "filters": {
    "year": "2024",
    "period": "Q1"
  }
}
```

### Get KPI Definitions

```bash
GET /api/v1/kpi/definitions
Authorization: Bearer <token>
```

### Drill Down

```bash
GET /api/v1/kpi/drill-down?kpi_id=revenue_total&filters={"region":"north"}
Authorization: Bearer <token>
```

## Configuration

### KPI Definitions

Add new KPIs in `src/kpi_bot/catalog/metric_catalog.py`:

```python
{
    "id": "new_kpi",
    "name": "New KPI",
    "description": "Description of the new KPI",
    "category": KPICategory.REVENUE,
    "calculation_type": CalculationType.SUM,
    "formula": "SUM(account_codes)",
    "unit": "currency",
    "currency": "USD",
    "data_sources": ["oracle_fusion_financials"],
    "refresh_frequency": "daily",
    "owner": "finance_team",
    "tags": ["revenue", "new"],
    "access_roles": [UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN],
    "oracle_mapping": {
        "source_system": "FCCS",
        "cube": "FCCS_Revenue",
        "account_filter": "Revenue_New"
    }
}
```

### Oracle Connection

Update connection settings in `src/kpi_bot/api/kpi_api.py`:

```python
def _get_oracle_connection():
    return OracleConnection(
        id="primary",
        name="Primary Oracle Connection",
        connection_type="EPM",
        host=os.getenv("ORACLE_EPM_HOST"),
        port=443,
        service_name="FCCS",
        username=os.getenv("ORACLE_EPM_USERNAME"),
        password=os.getenv("ORACLE_EPM_PASSWORD")
    )
```

## Development

### Project Structure

```
src/kpi_bot/
├── auth/                   # Authentication system
│   └── auth_manager.py
├── chat/                   # Natural language processing
│   ├── intent_detector.py
│   └── narrative_generator.py
├── catalog/                # Metric catalog (RAG)
│   └── metric_catalog.py
├── oracle/                 # Oracle EPM integration
│   └── epm_connector.py
├── calculations/           # KPI calculation engine
│   └── kpi_engine.py
├── visualizations/         # Chart generation
│   └── chart_generator.py
├── anomaly/               # Anomaly detection
│   └── anomaly_detector.py
├── dashboard/             # Streamlit UI
│   └── kpi_dashboard.py
├── api/                   # FastAPI endpoints
│   └── kpi_api.py
└── models.py              # Data models
```

### Adding New Features

1. **New KPI Type**: Update `models.py` and `metric_catalog.py`
2. **New Data Source**: Extend `epm_connector.py`
3. **New Calculation**: Add to `kpi_engine.py`
4. **New Visualization**: Extend `chart_generator.py`

### Testing

```bash
# Run tests
pytest tests/kpi_bot/

# Test specific component
pytest tests/kpi_bot/test_catalog.py
```

## Performance Optimization

### Caching Strategy

- **KPI Results**: 60-minute cache for calculations
- **Metric Catalog**: In-memory embedding cache
- **Oracle Data**: Connection pooling

### Monitoring

- **Response Times**: < 5 seconds for queries
- **Memory Usage**: Monitored via metrics
- **API Calls**: Rate limiting and logging

## Security

### Authentication

- JWT tokens with expiration
- Role-based access control
- SSO integration ready

### Data Protection

- Encryption in transit (TLS)
- Secure credential storage
- Audit logging for compliance

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Check Oracle EPM credentials
   - Verify network connectivity
   - Review firewall settings

2. **Query Failures**
   - Check KPI definitions
   - Verify data sources
   - Review Oracle mappings

3. **Performance Issues**
   - Clear calculation cache
   - Check database connections
   - Monitor memory usage

### Logs

```bash
# Application logs
tail -f logs/app.log

# KPI Bot specific logs
tail -f logs/kpi_bot/kpi_bot.log

# Error logs
tail -f logs/error.log
```

## Support

For technical support and feature requests:
- Create GitHub issues
- Contact development team
- Check documentation updates

## Roadmap

### Phase 2 (Q2 2024)
- Mobile-responsive interface
- Advanced anomaly detection
- Predictive analytics
- Multi-language support

### Phase 3 (Q3 2024)
- External BI integration
- Custom KPI builder
- Advanced governance features
- Real-time alerts

---

**KPI Insight Bot** - Empowering finance teams with conversational analytics.