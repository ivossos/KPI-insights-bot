# KPI Insight Bot - Deployment Guide

## Overview

This guide covers deploying the KPI Insight Bot system across different platforms. The system has been designed to work seamlessly on Replit, Docker, and traditional server environments.

## 🚀 Quick Start - Replit Deployment (Recommended)

### 1. Fork/Import to Replit

1. Go to [Replit](https://replit.com)
2. Click "Create Repl" → "Import from GitHub"
3. Use this repository URL: `https://github.com/your-username/ia-fiscal-capivari`

### 2. Configure Environment Variables

In Replit, go to the "Secrets" tab (🔒) and add these variables:

```
APIFY_API_TOKEN=apify_api_j1jWrugJ5rwkofSqd9vIlvgCYRkINA29hABh
CLAUDE_API_KEY=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
OPENAI_API_KEY=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
ANTHROPIC_API_KEY=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
GOOGLE_CLIENT_ID=961822477560-jlqoijtim2dc84hhhsjq981b76qo3v96.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
SMTP_USERNAME=ivossos@gmail.com
SMTP_PASSWORD=Rosy808120#
ADMIN_EMAIL=ivossos@gmail.com
SECRET_KEY=Nearshoring
SESSION_SECRET=Nearshoring
```

### 3. Run the Application

1. Click the "Run" button in Replit
2. The system will automatically:
   - Install dependencies
   - Start the API server (port 8000)
   - Start the KPI Dashboard (port 8501)
   - Configure the environment

### 4. Access the Application

- **KPI Dashboard**: `https://your-repl-name.your-username.repl.co`
- **API**: `https://your-repl-name.your-username.repl.co:8000`
- **Health Check**: `https://your-repl-name.your-username.repl.co:8000/health`

### 5. Login Credentials

Default demo accounts:
- **Admin**: `admin@company.com` / `admin123`
- **Analyst**: `analyst@company.com` / `analyst123`

## 🐳 Docker Deployment

### Prerequisites

- Docker and Docker Compose installed
- Minimum 4GB RAM, 20GB storage

### 1. Clone Repository

```bash
git clone https://github.com/your-username/ia-fiscal-capivari.git
cd ia-fiscal-capivari
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your actual values
```

### 3. Deploy with Docker Compose

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run full deployment
./deploy.sh deploy

# Check status
./deploy.sh status

# View logs
./deploy.sh logs
```

### 4. Alternative Docker Commands

```bash
# Build and start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

## 🖥️ Traditional Server Deployment

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx (optional)

### 1. System Setup

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql redis-server nginx

# CentOS/RHEL
sudo yum install python3 python3-pip postgresql redis nginx
```

### 2. Database Setup

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE kpi_bot;
CREATE USER kpi_user WITH PASSWORD 'kpi_password';
GRANT ALL PRIVILEGES ON DATABASE kpi_bot TO kpi_user;
\q

# Import schema
psql -U kpi_user -d kpi_bot -f init.sql
```

### 3. Application Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your values

# Create directories
mkdir -p data/{raw,processed,alerts} logs reports chroma_db
```

### 4. Run Application

```bash
# Start with production runner
python run_kpi_bot.py --mode complete

# Or run components separately
python run_kpi_bot.py --mode api &
python run_kpi_bot.py --mode dashboard &
```

### 5. Configure Nginx (Optional)

```bash
# Copy nginx config
sudo cp nginx.conf /etc/nginx/sites-available/kpi-bot
sudo ln -s /etc/nginx/sites-available/kpi-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key | Required |
| `ENVIRONMENT` | Environment (dev/prod) | `production` |
| `API_PORT` | API server port | `8000` |
| `DASHBOARD_PORT` | Dashboard port | `8502` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `CLAUDE_API_KEY` | Claude API key | Required |
| `ORACLE_EPM_HOST` | Oracle EPM host | Optional |
| `ORACLE_EPM_USERNAME` | Oracle EPM username | Optional |
| `ORACLE_EPM_PASSWORD` | Oracle EPM password | Optional |

### Oracle EPM Configuration

To connect to Oracle EPM systems:

```env
ORACLE_EPM_HOST=your-epm-host.company.com
ORACLE_EPM_PORT=443
ORACLE_EPM_USERNAME=your-username
ORACLE_EPM_PASSWORD=your-password
ORACLE_EPM_SERVICE_NAME=FCCS
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints

- **API Health**: `GET /health`
- **System Status**: `GET /api/v1/system/status`

### Monitoring Tools

```bash
# Run health check
python healthcheck.py

# Continuous monitoring
python healthcheck.py monitor 30

# View logs
tail -f logs/kpi_bot.log

# Check Docker containers
docker-compose ps
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process on port
   sudo lsof -t -i:8000 | xargs kill -9
   ```

2. **Database Connection Error**
   ```bash
   # Check database status
   pg_isready -h localhost -p 5432
   
   # Test connection
   psql -U kpi_user -d kpi_bot -h localhost
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --force-reinstall
   ```

4. **API Keys Not Working**
   - Verify keys in environment variables
   - Check API key permissions
   - Test with simple API calls

### Logs

```bash
# Application logs
tail -f logs/app.log

# Error logs
tail -f logs/error.log

# KPI Bot specific logs
tail -f logs/kpi_bot.log

# Docker logs
docker-compose logs -f kpi-bot
```

## 🔒 Security

### Production Security Checklist

- [ ] Change default passwords
- [ ] Use environment variables for secrets
- [ ] Enable SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Monitor access logs
- [ ] Update dependencies regularly

### SSL/TLS Setup

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes

# Or use Let's Encrypt
certbot --nginx -d your-domain.com
```

## 🚀 Scaling

### Performance Optimization

1. **Database Optimization**
   - Use connection pooling
   - Enable query caching
   - Add database indexes

2. **Caching**
   - Redis for session storage
   - Application-level caching
   - API response caching

3. **Load Balancing**
   - Multiple API instances
   - Nginx load balancing
   - Database read replicas

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  kpi-bot:
    deploy:
      replicas: 3
    
  nginx:
    depends_on:
      - kpi-bot
    deploy:
      replicas: 2
```

## 📈 Maintenance

### Regular Tasks

1. **Daily**
   - Check system health
   - Monitor error logs
   - Verify API responses

2. **Weekly**
   - Update dependencies
   - Review performance metrics
   - Check database size

3. **Monthly**
   - Security updates
   - Backup verification
   - Performance optimization

### Backup Strategy

```bash
# Database backup
pg_dump -U kpi_user kpi_bot > backup_$(date +%Y%m%d).sql

# Application backup
tar -czf backup_$(date +%Y%m%d).tar.gz data/ logs/ chroma_db/
```

## 📞 Support

### Getting Help

1. **Documentation**: Check this guide and `KPI_BOT_README.md`
2. **Logs**: Review application logs for errors
3. **Health Check**: Run `python healthcheck.py`
4. **Community**: Create GitHub issues for bugs/features

### Contact Information

- **Email**: ivossos@gmail.com
- **GitHub**: [Repository Issues](https://github.com/your-username/ia-fiscal-capivari/issues)

---

**KPI Insight Bot** - Deployment completed successfully! 🎉