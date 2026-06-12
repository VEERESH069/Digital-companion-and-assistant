# Production Deployment Guide - Pre-Visit Voice Agent

## Pre-Deployment Checklist

### Security
- [ ] Remove all API keys from code and `.env` file
- [ ] Use a secrets management system (AWS Secrets Manager, HashiCorp Vault, etc.)
- [ ] Generate a strong `SECRET_KEY` for Flask
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Set `FLASK_DEBUG=false` in production
- [ ] Set `FLASK_ENV=production`
- [ ] Use environment variables for all sensitive configuration
- [ ] Enable CORS only for trusted domains
- [ ] Implement rate limiting
- [ ] Add authentication/authorization (JWT tokens)
- [ ] Set up API key rotation policy

### Configuration
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up proper logging (not to stdout for production)
- [ ] Enable error tracking (Sentry or similar)
- [ ] Configure backup strategy
- [ ] Set appropriate resource limits

### Testing
- [ ] Run full test suite: `pytest tests/`
- [ ] Run security checks: `bandit -r .`
- [ ] Check code quality: `flake8 . && black --check .`
- [ ] Performance test with production-like data
- [ ] Test all supported languages (en, hi, mr, te, bn, ta, ml)

### Infrastructure
- [ ] Set up PostgreSQL database
- [ ] Configure monitoring and alerting
- [ ] Set up log aggregation
- [ ] Configure auto-scaling if needed
- [ ] Set up CDN for static files (if applicable)
- [ ] Configure WAF (Web Application Firewall)

## Step 1: Update Environment Variables

```bash
# Copy template to actual env file
cp .env.example .env

# Edit .env with production values
# Make sure to use secure secrets management:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
# - GitHub Secrets (for CI/CD)
```

## Step 2: Database Setup

### Using PostgreSQL

```bash
# Create database and user
createdb previsit_agent
createuser previsit_user -P

# Run migrations
alembic upgrade head
```

### Connection string format
```
postgresql://previsit_user:password@hostname:5432/previsit_agent
```

## Step 3: Docker Deployment

```bash
# Build production image
docker build -t previsit-agent:latest .

# Run container with environment variables
docker run -d \
  --name previsit-agent \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e CARTESIA_API_KEY="${CARTESIA_API_KEY}" \
  -e DATABASE_URL="${DATABASE_URL}" \
  -e FLASK_ENV=production \
  -p 5000:5000 \
  previsit-agent:latest

# Health check
curl http://localhost:5000/health
```

## Step 4: Kubernetes Deployment

```yaml
# See kubernetes/ directory for full manifests
# Update with your registry and resource requirements
kubectl apply -f kubernetes/
```

## Step 5: Enable Monitoring

### Application Monitoring
```python
# Sentry (error tracking)
import sentry_sdk
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT")
)

# Prometheus metrics
from prometheus_client import Counter, Histogram
```

### Infrastructure Monitoring
- [ ] Set up CloudWatch/DataDog/New Relic
- [ ] Configure alerts for:
  - High error rates
  - High latency
  - Database connection issues
  - Low disk space

## Step 6: Backup & Recovery

```bash
# Database backup schedule
0 2 * * * pg_dump previsit_agent | gzip > /backups/db_backup_$(date +\%Y\%m\%d).sql.gz

# Data directory backup
0 3 * * * tar -czf /backups/data_backup_$(date +\%Y\%m\%d).tar.gz ./data/
```

## Step 7: SSL/TLS Configuration

```bash
# Get SSL certificate (Let's Encrypt)
certbot certonly --standalone -d yourdomain.com

# Configure in Nginx/Apache reverse proxy
# Redirect HTTP to HTTPS
# Add security headers (HSTS, CSP, etc.)
```

## Step 8: Load Balancing

```nginx
# Example Nginx configuration
upstream previsit_agent {
    server app1:5000;
    server app2:5000;
    server app3:5000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://previsit_agent;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Step 9: Performance Optimization

```python
# In config.py
ENABLE_TTS_CACHING = True
PRELOAD_TTS_MODEL = False  # Load on demand
USE_GPU = True  # If available

# Gunicorn settings for production
--workers 4              # 2-4 * CPU cores
--worker-class sync      # or gevent for async
--timeout 120
--max-requests 1000
--max-requests-jitter 100
```

## Step 10: Log Aggregation

```python
# Using python-json-logger for structured logs
import json
from pythonjsonlogger import jsonlogger

logHandler = logging.FileHandler(filename='./logs/production.log')
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
```

## Monitoring Commands

```bash
# Check application health
curl https://yourdomain.com/health

# View logs
tail -f ./logs/production.log | jq .

# Database status
psql previsit_agent -c "SELECT * FROM conversation_sessions LIMIT 10;"

# Monitor active sessions
watch -n 5 'curl -s https://yourdomain.com/api/stats | jq .'
```

## Rollback Procedure

```bash
# If deployment fails, rollback to previous version
docker run -d --name previsit-agent-old \
  previsit-agent:v1.0.0

# Or with Kubernetes
kubectl rollout undo deployment/previsit-agent
```

## Security Hardening Checklist

- [ ] HTTPS/TLS enabled
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (using SQLAlchemy ORM)
- [ ] CSRF protection enabled
- [ ] Security headers configured:
  - `Strict-Transport-Security`
  - `Content-Security-Policy`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
- [ ] API key rotation policy
- [ ] Access logging enabled
- [ ] WAF rules configured
- [ ] DDoS protection enabled
- [ ] Secrets not in logs or error messages

## Scaling Considerations

1. **Horizontal Scaling**: Use load balancer (Nginx, AWS ALB)
2. **Vertical Scaling**: Increase CPU/RAM for GPU models
3. **Caching**: Use Redis for session/model caching
4. **Database**: Use read replicas for high traffic
5. **Async Tasks**: Use Celery for long-running operations

## Support & Maintenance

- [ ] Set up on-call rotation
- [ ] Create runbooks for common issues
- [ ] Set up automated patching
- [ ] Regular security audits
- [ ] Performance profiling
- [ ] Dependency updates
- [ ] Database optimization (index review)

## Emergency Contacts

- [ ] On-call engineer: ________
- [ ] Database admin: ________
- [ ] DevOps team: ________
- [ ] Security team: ________

## Production Support

For issues or questions:
1. Check logs: `tail -f ./logs/production.log`
2. Check health: `curl https://yourdomain.com/health`
3. Contact on-call engineer
4. Check recent deployments
5. Review error tracking (Sentry)
