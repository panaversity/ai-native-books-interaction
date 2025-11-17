# Deployment Guide

This guide covers deployment strategies for the AI Native Books Interaction API.

## Table of Contents

- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring & Maintenance](#monitoring--maintenance)

## Local Development

### Quick Start

1. **Setup virtual environment**
   ```bash
   cd api
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```
   
   Edit `.env` and add your `GOOGLE_API_KEY`

4. **Run development server**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## Production Deployment

### Prerequisites

- Python 3.11+
- Process manager (systemd, supervisor, or PM2)
- Reverse proxy (Nginx or Caddy)
- SSL certificate (Let's Encrypt recommended)
- Domain name

### Step-by-Step Production Setup

#### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx -y

# Create application user
sudo useradd -m -s /bin/bash appuser
```

#### 2. Application Setup

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/panaversity/ai-native-books-interaction.git
sudo chown -R appuser:appuser ai-native-books-interaction

# Switch to app user
sudo su - appuser
cd /opt/ai-native-books-interaction/api

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Edit with production values
```

#### 3. Systemd Service

Create `/etc/systemd/system/ai-books-api.service`:

```ini
[Unit]
Description=AI Native Books Interaction API
After=network.target

[Service]
Type=exec
User=appuser
Group=appuser
WorkingDirectory=/opt/ai-native-books-interaction/api
Environment="PATH=/opt/ai-native-books-interaction/api/venv/bin"
EnvironmentFile=/opt/ai-native-books-interaction/api/.env
ExecStart=/opt/ai-native-books-interaction/api/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-books-api
sudo systemctl start ai-books-api
sudo systemctl status ai-books-api
```

#### 4. Nginx Configuration

Create `/etc/nginx/sites-available/ai-books-api`:

```nginx
upstream ai_books_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
    
    # Max upload size
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://ai_books_backend;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE support
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://ai_books_backend;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/ai-books-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. SSL Certificate

```bash
sudo certbot --nginx -d api.yourdomain.com
```

#### 6. Firewall Configuration

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

## Docker Deployment

### Dockerfile

Create `api/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - CORS_ORIGINS=${CORS_ORIGINS}
    volumes:
      - ./api/logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - ai-books-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - ai-books-network

networks:
  ai-books-network:
    driver: bridge
```

### Running with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

## Cloud Deployment

### AWS (EC2 + ECS)

#### EC2 Deployment

1. Launch EC2 instance (Ubuntu 22.04, t3.medium or larger)
2. Configure security group:
   - Port 22 (SSH)
   - Port 80 (HTTP)
   - Port 443 (HTTPS)
3. Follow [Production Deployment](#production-deployment) steps

#### ECS (Elastic Container Service)

1. **Push image to ECR**
   ```bash
   aws ecr create-repository --repository-name ai-books-api
   docker build -t ai-books-api ./api
   docker tag ai-books-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/ai-books-api:latest
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/ai-books-api:latest
   ```

2. **Create ECS Task Definition** (`task-definition.json`)
   ```json
   {
     "family": "ai-books-api",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "containerDefinitions": [{
       "name": "api",
       "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/ai-books-api:latest",
       "portMappings": [{
         "containerPort": 8000,
         "protocol": "tcp"
       }],
       "environment": [
         {"name": "LOG_LEVEL", "value": "INFO"}
       ],
       "secrets": [
         {"name": "GOOGLE_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
       ]
     }]
   }
   ```

3. **Create ECS Service with ALB**

### Google Cloud Platform (Cloud Run)

1. **Build and push to GCR**
   ```bash
   gcloud builds submit --tag gcr.io/<project-id>/ai-books-api ./api
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy ai-books-api \
     --image gcr.io/<project-id>/ai-books-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars LOG_LEVEL=INFO \
     --set-secrets GOOGLE_API_KEY=google-api-key:latest \
     --memory 1Gi \
     --cpu 2 \
     --max-instances 10
   ```

### Azure (Container Instances / App Service)

#### Container Instances
```bash
az container create \
  --resource-group ai-books-rg \
  --name ai-books-api \
  --image <registry>.azurecr.io/ai-books-api:latest \
  --dns-name-label ai-books-api \
  --ports 8000 \
  --environment-variables LOG_LEVEL=INFO \
  --secure-environment-variables GOOGLE_API_KEY=<key>
```

## Environment Configuration

### Production Environment Variables

```env
# API Configuration
GOOGLE_API_KEY=<production-key>
LOG_LEVEL=INFO
CORS_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Security (future)
JWT_SECRET_KEY=<random-256-bit-key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Database (future)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (future)
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=50

# Monitoring
SENTRY_DSN=<sentry-dsn>
```

### Secrets Management

**AWS Secrets Manager**:
```bash
aws secretsmanager create-secret \
  --name ai-books/google-api-key \
  --secret-string "your-api-key"
```

**GCP Secret Manager**:
```bash
echo -n "your-api-key" | gcloud secrets create google-api-key --data-file=-
```

**Azure Key Vault**:
```bash
az keyvault secret set \
  --vault-name ai-books-vault \
  --name google-api-key \
  --value "your-api-key"
```

## Monitoring & Maintenance

### Health Checks

```bash
# Basic health check
curl https://api.yourdomain.com/health

# Expected response
{
  "status": "healthy",
  "service": "content-personalization-api",
  "api_configured": true
}
```

### Log Management

```bash
# Systemd logs
sudo journalctl -u ai-books-api -f

# Docker logs
docker-compose logs -f api

# Application logs
tail -f /opt/ai-native-books-interaction/api/logs/app.log
```

### Performance Monitoring

Monitor these metrics:
- Request latency (target: p95 < 2s)
- Error rate (target: < 1%)
- CPU usage (target: < 70%)
- Memory usage (target: < 80%)
- Active connections

### Backup Strategy

1. **Database backups** (future):
   - Automated daily backups
   - Point-in-time recovery enabled
   - Retention: 30 days

2. **Configuration backups**:
   ```bash
   # Backup .env and configs
   tar -czf backup-$(date +%Y%m%d).tar.gz .env nginx/
   ```

### Updates & Rollback

```bash
# Update application
cd /opt/ai-native-books-interaction
sudo -u appuser git pull
sudo -u appuser /opt/ai-native-books-interaction/api/venv/bin/pip install -r api/requirements.txt
sudo systemctl restart ai-books-api

# Rollback
sudo -u appuser git checkout <previous-commit>
sudo systemctl restart ai-books-api
```

### Scaling Strategies

1. **Vertical Scaling**: Increase server resources
2. **Horizontal Scaling**: Add more instances behind load balancer
3. **Auto-scaling**: Based on CPU/memory/request metrics

### Troubleshooting

Common issues and solutions:

1. **Service won't start**
   ```bash
   sudo systemctl status ai-books-api
   sudo journalctl -u ai-books-api -n 50
   ```

2. **High memory usage**
   - Reduce worker count
   - Check for memory leaks
   - Implement connection pooling

3. **Slow responses**
   - Check Gemini API latency
   - Enable caching
   - Optimize database queries

4. **SSL issues**
   ```bash
   sudo certbot renew --dry-run
   sudo systemctl reload nginx
   ```

## Security Checklist

- [ ] SSL/TLS enabled
- [ ] Firewall configured
- [ ] API keys in secrets manager
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Regular security updates
- [ ] Log monitoring active
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented

## Support

For deployment issues:
1. Check logs first
2. Review documentation
3. Open GitHub issue
4. Contact maintainers

---

**Last Updated**: November 2025  
**Version**: 1.0.0
