# Deployment Guide

## Prerequisites

### System Requirements
- Python 3.10+
- PostgreSQL 13+
- 8GB RAM minimum (16GB recommended)
- 50GB storage minimum

### Dependencies
- PostgreSQL with pgvector extension
- Python virtual environment (recommended)

## Environment Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd knowledge_base
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS with Homebrew
brew install postgresql
brew services start postgresql

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
```

#### Create Database and User
```bash
sudo -u postgres psql

# In PostgreSQL shell
CREATE DATABASE knowledge_base;
CREATE USER kb_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE knowledge_base TO kb_user;
\q
```

#### Enable pgvector Extension
```bash
sudo -u postgres psql -d knowledge_base
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\q
```

#### Initialize Schema
```bash
psql -d knowledge_base -f schema.sql
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```bash
# Database Configuration
DB_USER=kb_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=knowledge_base

# LLM Configuration
GOOGLE_API_KEY=your_google_api_key
LLM_MODEL=gemini-2.5-flash
LLM_PROVIDER=google

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# Streamlit Configuration
STREAMLIT_API_URL=http://localhost:8000
STREAMLIT_WS_URL=ws://localhost:8000/ws

# Logging
LOG_LEVEL=INFO
```

## Deployment Options

### Development Deployment

#### Start API Server
```bash
python main_api.py
```

#### Start Web Interface
```bash
cd streamlit-ui
streamlit run app.py
```

### Production Deployment

#### Using systemd (Linux)

Create service files:

**API Service** (`/etc/systemd/system/knowledge-base-api.service`):
```ini
[Unit]
Description=Knowledge Base API Server
After=network.target postgresql.service

[Service]
Type=simple
User=kb-user
WorkingDirectory=/path/to/knowledge_base
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python main_api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Streamlit Service** (`/etc/systemd/system/knowledge-base-ui.service`):
```ini
[Unit]
Description=Knowledge Base Streamlit UI
After=network.target knowledge-base-api.service

[Service]
Type=simple
User=kb-user
WorkingDirectory=/path/to/knowledge_base/streamlit-ui
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable knowledge-base-api
sudo systemctl enable knowledge-base-ui
sudo systemctl start knowledge-base-api
sudo systemctl start knowledge-base-ui
```

#### Using Docker

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000
CMD ["python", "main_api.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: knowledge_base
      POSTGRES_USER: kb_user
      POSTGRES_PASSWORD: your_secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"

  api:
    build: .
    environment:
      - DB_HOST=db
      - DB_USER=kb_user
      - DB_PASSWORD=your_secure_password
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - db

  ui:
    build:
      context: .
      dockerfile: Dockerfile.ui
    environment:
      - STREAMLIT_API_URL=http://api:8000
    ports:
      - "8501:8501"
    depends_on:
      - api

volumes:
  postgres_data:
```

**Dockerfile.ui**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app/streamlit-ui

COPY streamlit-ui/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit-ui/ .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

### Cloud Deployment

#### AWS EC2
1. Launch EC2 instance (t3.medium or larger)
2. Install dependencies as above
3. Configure security groups for ports 8000, 8501, 5432
4. Use AWS Systems Manager for secrets management

#### Google Cloud Run
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/knowledge-base', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/knowledge-base']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'knowledge-base'
      - '--image'
      - 'gcr.io/$PROJECT_ID/knowledge-base'
      - '--platform'
      - 'managed'
      - '--port'
      - '8000'
      - '--allow-unauthenticated'
```

## Monitoring and Maintenance

### Health Checks
```bash
# API health check
curl http://localhost:8000/api/stats

# Database connectivity
psql -d knowledge_base -c "SELECT COUNT(*) FROM nodes;"
```

### Logs
```bash
# View API logs
journalctl -u knowledge-base-api -f

# View UI logs
journalctl -u knowledge-base-ui -f
```

### Backup Strategy
```bash
# Database backup
pg_dump knowledge_base > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/var/backups/knowledge_base"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump knowledge_base > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

### Performance Tuning

#### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_nodes_type ON nodes(type);
CREATE INDEX CONCURRENTLY idx_edges_type ON edges(type);
CREATE INDEX CONCURRENTLY idx_events_timestamp ON events(timestamp);

-- Analyze tables for query optimization
ANALYZE nodes;
ANALYZE edges;
ANALYZE communities;
```

#### Memory Configuration
```bash
# Increase PostgreSQL shared memory
echo "shared_preload_libraries = 'pg_stat_statements'" >> /etc/postgresql/postgresql.conf
echo "pg_stat_statements.max = 10000" >> /etc/postgresql/postgresql.conf
echo "pg_stat_statements.track = all" >> /etc/postgresql/postgresql.conf
```

## Security Considerations

### Network Security
- Use HTTPS in production
- Configure firewall rules
- Use VPC/security groups

### Application Security
- Implement authentication/authorization
- Use environment variables for secrets
- Regular dependency updates
- Input validation and sanitization

### Database Security
- Use strong passwords
- Limit database user privileges
- Enable SSL connections
- Regular security updates

## Troubleshooting

### Common Issues

#### API Server Won't Start
```bash
# Check database connectivity
psql -h localhost -U kb_user -d knowledge_base

# Check environment variables
python -c "import os; print(os.environ.get('DB_USER'))"

# Check logs
python main_api.py 2>&1 | tee api.log
```

#### Out of Memory Errors
```bash
# Increase system memory or optimize queries
# Check memory usage
ps aux --sort=-%mem | head

# Monitor PostgreSQL memory
psql -d knowledge_base -c "SELECT * FROM pg_stat_activity;"
```

#### Slow Performance
```bash
# Check query performance
psql -d knowledge_base -c "EXPLAIN ANALYZE SELECT * FROM nodes LIMIT 100;"

# Check system resources
top
iotop
```

## Scaling Considerations

### Horizontal Scaling
- Multiple API server instances behind load balancer
- Read replicas for database
- Redis for session management

### Vertical Scaling
- Increase instance size for memory/CPU intensive operations
- SSD storage for better I/O performance

### Data Partitioning
- Partition large tables by time or entity type
- Archive old data to separate tables