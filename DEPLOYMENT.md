# Deployment Guide

This guide covers deploying the Trading Portfolio What-If Analysis System to production environments (AWS, GCP, Azure, or self-hosted infrastructure).

## System Requirements

### Dependencies
- Python 3.11+
- PostgreSQL 14+
- Required Python packages (see requirements.txt):
  - streamlit>=1.51.0
  - pandas>=2.3.3
  - numpy>=2.3.4
  - plotly>=6.4.0
  - scipy>=1.16.3
  - matplotlib>=3.10.7
  - seaborn>=0.13.2
  - psycopg2-binary>=2.9.11
  - python-dotenv>=1.2.1

### Environment Variables

The application requires the following environment variables:

```bash
PGHOST=postgres.example.com
PGPORT=5432
PGDATABASE=trading_db
PGUSER=postgres
PGPASSWORD=your-secure-password
SESSION_SECRET=your-random-secret-key-here
```

**PostgreSQL Connection:**
The application uses individual PostgreSQL environment variables (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD) instead of a single DATABASE_URL connection string.

## Docker Deployment

### Build the Docker Image

```bash
docker build -t trading-portfolio-analysis:latest .
```

**Verify the Build:**
After building, test that all scientific libraries import correctly:

```bash
# Test Python imports
docker run --rm trading-portfolio-analysis:latest python -c "import numpy, scipy, pandas, streamlit, plotly, matplotlib, seaborn; print('✅ All imports successful')"

# Test database connection readiness (will fail without DB, but tests import)
docker run --rm trading-portfolio-analysis:latest python -c "import psycopg2; print('✅ PostgreSQL client ready')"
```

If you see any import errors, ensure all system libraries are installed correctly in the Dockerfile.

### Run with Docker

```bash
docker run -d \
  --name trading-app \
  -p 5000:5000 \
  -e PGHOST="postgres.example.com" \
  -e PGPORT="5432" \
  -e PGDATABASE="trading_db" \
  -e PGUSER="postgres" \
  -e PGPASSWORD="your-secure-password" \
  -e SESSION_SECRET="your-secret-key" \
  trading-portfolio-analysis:latest
```

### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: secure_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trading_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      PGHOST: postgres
      PGPORT: 5432
      PGDATABASE: trading_db
      PGUSER: trading_user
      PGPASSWORD: secure_password_here
      SESSION_SECRET: your-random-secret-key-here
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

Deploy with:
```bash
docker-compose up -d
```

Access the application at: http://localhost:5000

## AWS Deployment Options

### Option 1: AWS ECS (Elastic Container Service)

**Prerequisites:**
- AWS CLI installed and configured
- ECR repository created
- ECS cluster created
- RDS PostgreSQL instance running

**Steps:**

1. **Push image to ECR:**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

docker tag trading-portfolio-analysis:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/trading-portfolio-analysis:latest

docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/trading-portfolio-analysis:latest
```

2. **Create ECS Task Definition:**
```json
{
  "family": "trading-portfolio-analysis",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/trading-portfolio-analysis:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PGHOST",
          "value": "your-rds-endpoint.region.rds.amazonaws.com"
        },
        {
          "name": "PGPORT",
          "value": "5432"
        },
        {
          "name": "PGDATABASE",
          "value": "trading_db"
        },
        {
          "name": "PGUSER",
          "value": "postgres"
        },
        {
          "name": "PGPASSWORD",
          "value": "your-secure-password"
        },
        {
          "name": "SESSION_SECRET",
          "value": "your-secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/trading-portfolio-analysis",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "512",
  "memory": "1024"
}
```

3. **Create ECS Service:**
```bash
aws ecs create-service \
  --cluster your-cluster \
  --service-name trading-portfolio-analysis \
  --task-definition trading-portfolio-analysis \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Option 2: AWS EC2

1. **Launch EC2 instance (Ubuntu 22.04 LTS)**

2. **Install dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose postgresql-client git

sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
```

3. **Clone and deploy:**
```bash
git clone YOUR_REPOSITORY
cd trading-portfolio-analysis

# Set environment variables
export PGHOST="your-rds-endpoint.region.rds.amazonaws.com"
export PGPORT="5432"
export PGDATABASE="trading_db"
export PGUSER="postgres"
export PGPASSWORD="your-secure-password"
export SESSION_SECRET="your-secret-key"

# Run with Docker Compose
docker-compose up -d
```

4. **Configure security group:**
- Allow inbound traffic on port 5000 (or use nginx reverse proxy on port 80/443)

### Option 3: AWS Lightsail (Simplest)

1. Create Lightsail container service
2. Push Docker image
3. Configure environment variables
4. Deploy

## GCP Deployment (Cloud Run)

**Prerequisites:**
- gcloud CLI installed
- Cloud SQL PostgreSQL instance created

**Deploy:**

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/YOUR_PROJECT/trading-portfolio-analysis

# Deploy to Cloud Run
gcloud run deploy trading-portfolio-analysis \
  --image gcr.io/YOUR_PROJECT/trading-portfolio-analysis \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PGHOST="/cloudsql/PROJECT:REGION:INSTANCE" \
  --set-env-vars PGPORT="5432" \
  --set-env-vars PGDATABASE="trading_db" \
  --set-env-vars PGUSER="postgres" \
  --set-env-vars PGPASSWORD="your-secure-password" \
  --set-env-vars SESSION_SECRET="your-secret-key"
```

## Azure Deployment (Container Instances)

```bash
# Create resource group
az group create --name trading-rg --location eastus

# Create Azure Database for PostgreSQL
az postgres server create --resource-group trading-rg --name trading-db --location eastus --admin-user adminuser --admin-password Password123! --sku-name B_Gen5_1

# Deploy container
az container create \
  --resource-group trading-rg \
  --name trading-app \
  --image YOUR_ACR.azurecr.io/trading-portfolio-analysis:latest \
  --dns-name-label trading-portfolio \
  --ports 5000 \
  --environment-variables PGHOST="trading-db.postgres.database.azure.com" PGPORT="5432" PGDATABASE="postgres" PGUSER="adminuser@trading-db" PGPASSWORD="Password123!" SESSION_SECRET="your-secret-key"
```

## Database Setup

### Initial Database Creation

The application automatically creates all required tables on first startup. Ensure your PostgreSQL database exists and the user has CREATE TABLE permissions.

**Required Tables:**
- `machines` - Trading machine/account configurations
- `trades` - Trade history data
- `market_data` - OHLCV market data (shared across machines)
- `scenarios` - What-if scenario configurations
- `scenario_results` - Cached scenario results

### Database Migrations

This application does not use traditional migrations. Schema changes are applied automatically by the application on startup.

**For production environments:**
1. Back up your database before updates
2. Test schema changes in staging environment
3. Review database.py for any schema modifications

## Environment-Specific Configuration

### Production Settings

Add to `.streamlit/config.toml`:

```toml
[server]
port = 5000
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "your-domain.com"
serverPort = 443

[theme]
base = "light"
```

### SSL/TLS (Production)

Use a reverse proxy (nginx, traefik, or cloud load balancer) for SSL termination:

**nginx example:**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring & Logging

### Health Check Endpoint

The Docker container includes a health check at `http://localhost:5000/_stcore/health`

### Application Logs

View Docker logs:
```bash
docker logs -f trading-app
```

For ECS:
```bash
aws logs tail /ecs/trading-portfolio-analysis --follow
```

### Database Monitoring

Monitor PostgreSQL performance:
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Database size
SELECT pg_size_pretty(pg_database_size('trading_db'));
```

## Scaling Considerations

### Horizontal Scaling

- Deploy multiple container instances behind a load balancer
- All state is stored in PostgreSQL (no session state on app servers)
- Consider connection pooling (PgBouncer) for high-concurrency environments

### Database Optimization

For 50+ machines with extensive trade history:

1. **Indexes** (already included in schema):
   - `machines.id` (primary key)
   - `trades.machine_id` (foreign key)
   - `market_data.symbol, timeframe, timestamp` (composite)

2. **Partitioning** (for very large datasets):
```sql
-- Partition trades by machine_id if needed
CREATE TABLE trades_partitioned (LIKE trades INCLUDING ALL)
PARTITION BY HASH (machine_id);
```

3. **Connection Pooling**:
```bash
# Use PgBouncer for connection pooling
export PGHOST="pgbouncer-host"
export PGPORT="6432"
export PGDATABASE="trading_db"
export PGUSER="postgres"
export PGPASSWORD="your-secure-password"
```

## Backup & Recovery

### Automated Backups (AWS RDS example)

```bash
# Enable automated backups
aws rds modify-db-instance \
  --db-instance-identifier trading-db \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00"
```

### Manual Backup

```bash
# Backup
pg_dump -h your-db-host -U user -d trading_db > backup_$(date +%Y%m%d).sql

# Restore
psql -h your-db-host -U user -d trading_db < backup_20251117.sql
```

## Security Best Practices

1. **Environment Variables**: Use secrets management (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
2. **Database Access**: Restrict to application subnet only
3. **Network Security**: Use VPC/private networking
4. **SSL/TLS**: Always use HTTPS in production
5. **Authentication**: Consider adding Streamlit authentication for multi-user deployments
6. **Regular Updates**: Keep dependencies updated for security patches

## Troubleshooting

### Database Connection Issues

```python
# Test database connection
import psycopg2
import os

try:
    conn = psycopg2.connect(
        host=os.environ['PGHOST'],
        port=os.environ['PGPORT'],
        database=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD']
    )
    print("✅ Database connection successful")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

### Container Issues

```bash
# Check container status
docker ps -a

# View logs
docker logs trading-app

# Interactive shell
docker exec -it trading-app /bin/bash
```

### Performance Issues

- Monitor database query performance
- Check container resource limits (CPU/memory)
- Review Streamlit session state size
- Consider caching strategies for frequently accessed data

## Cost Optimization

### AWS Cost Estimates

**Option 1: ECS Fargate + RDS**
- ECS Fargate (0.5 vCPU, 1GB): ~$15/month
- RDS PostgreSQL (db.t3.micro): ~$15/month
- **Total: ~$30/month**

**Option 2: EC2 + RDS**
- EC2 t3.small: ~$15/month
- RDS PostgreSQL (db.t3.micro): ~$15/month
- **Total: ~$30/month**

**Option 3: Lightsail**
- Lightsail container (512MB): ~$7/month
- Lightsail database (1GB): ~$15/month
- **Total: ~$22/month**

### GCP Cost Estimates

**Cloud Run + Cloud SQL**
- Cloud Run (always-on, 1 instance): ~$10/month
- Cloud SQL (db-f1-micro): ~$10/month
- **Total: ~$20/month**

## Support

For deployment issues or questions, refer to:
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
