# GrantThrive Deployment Guide

This guide provides comprehensive instructions for deploying GrantThrive to production environments, with specific focus on AWS deployment for Australian councils.

## 🎯 Deployment Overview

GrantThrive is designed for enterprise deployment with:
- **High availability** and scalability
- **Government-grade security** compliance
- **Australian data residency** requirements
- **Professional monitoring** and backup

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   Route 53      │    │   Certificate   │
│   (CDN)         │    │   (DNS)         │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│                    Application Load Balancer                     │
└─────────────────────────────────┼─────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EC2 Instance  │    │   EC2 Instance  │    │   EC2 Instance  │
│   (Frontend)    │    │   (Backend)     │    │   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   RDS Database  │
                    │   (PostgreSQL)  │
                    └─────────────────┘
```

## 🚀 AWS Production Deployment

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **Domain name** (e.g., grantthrive.com)
3. **SSL Certificate** for HTTPS
4. **AWS CLI** configured locally

### Step 1: Infrastructure Setup

#### 1.1 VPC and Networking
```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=GrantThrive-VPC}]'

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxxxxxxx --cidr-block 10.0.1.0/24 --availability-zone ap-southeast-2a
aws ec2 create-subnet --vpc-id vpc-xxxxxxxx --cidr-block 10.0.2.0/24 --availability-zone ap-southeast-2b

# Create Internet Gateway
aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=GrantThrive-IGW}]'
```

#### 1.2 Security Groups
```bash
# Web server security group
aws ec2 create-security-group \
  --group-name GrantThrive-Web \
  --description "GrantThrive Web Servers" \
  --vpc-id vpc-xxxxxxxx

# Database security group
aws ec2 create-security-group \
  --group-name GrantThrive-DB \
  --description "GrantThrive Database" \
  --vpc-id vpc-xxxxxxxx
```

#### 1.3 RDS Database Setup
```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name grantthrive-db-subnet \
  --db-subnet-group-description "GrantThrive DB Subnet Group" \
  --subnet-ids subnet-xxxxxxxx subnet-yyyyyyyy

# Create PostgreSQL database
aws rds create-db-instance \
  --db-instance-identifier grantthrive-prod \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 13.7 \
  --master-username grantthrive \
  --master-user-password [SECURE_PASSWORD] \
  --allocated-storage 100 \
  --storage-type gp2 \
  --vpc-security-group-ids sg-xxxxxxxx \
  --db-subnet-group-name grantthrive-db-subnet \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted
```

### Step 2: Application Deployment

#### 2.1 Backend Deployment

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY run.py .

EXPOSE 5000

CMD ["python", "run.py"]
```

Create `backend/run.py`:
```python
import os
from src.main import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

Build and deploy:
```bash
# Build Docker image
docker build -t grantthrive-backend ./backend

# Tag for ECR
docker tag grantthrive-backend:latest [ACCOUNT_ID].dkr.ecr.ap-southeast-2.amazonaws.com/grantthrive-backend:latest

# Push to ECR
docker push [ACCOUNT_ID].dkr.ecr.ap-southeast-2.amazonaws.com/grantthrive-backend:latest
```

#### 2.2 Frontend Deployment

Create `frontend/Dockerfile`:
```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Create `frontend/nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api {
            proxy_pass http://backend:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

#### 2.3 Docker Compose for Production

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - NODE_ENV=production

  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://grantthrive:[PASSWORD]@[RDS_ENDPOINT]:5432/grantthrive
      - JWT_SECRET_KEY=[SECURE_JWT_SECRET]
      - CORS_ORIGINS=https://grantthrive.com
    depends_on:
      - redis

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Step 3: Load Balancer and Auto Scaling

#### 3.1 Application Load Balancer
```bash
# Create load balancer
aws elbv2 create-load-balancer \
  --name GrantThrive-ALB \
  --subnets subnet-xxxxxxxx subnet-yyyyyyyy \
  --security-groups sg-xxxxxxxx

# Create target group
aws elbv2 create-target-group \
  --name GrantThrive-TG \
  --protocol HTTP \
  --port 80 \
  --vpc-id vpc-xxxxxxxx \
  --health-check-path /api/health
```

#### 3.2 Auto Scaling Group
```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name GrantThrive-Template \
  --launch-template-data '{
    "ImageId": "ami-xxxxxxxx",
    "InstanceType": "t3.medium",
    "SecurityGroupIds": ["sg-xxxxxxxx"],
    "UserData": "[BASE64_ENCODED_STARTUP_SCRIPT]"
  }'

# Create auto scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name GrantThrive-ASG \
  --launch-template LaunchTemplateName=GrantThrive-Template,Version=1 \
  --min-size 2 \
  --max-size 6 \
  --desired-capacity 2 \
  --vpc-zone-identifier "subnet-xxxxxxxx,subnet-yyyyyyyy" \
  --target-group-arns arn:aws:elasticloadbalancing:ap-southeast-2:[ACCOUNT]:targetgroup/GrantThrive-TG/xxxxxxxx
```

### Step 4: SSL and Domain Configuration

#### 4.1 SSL Certificate
```bash
# Request SSL certificate
aws acm request-certificate \
  --domain-name grantthrive.com \
  --subject-alternative-names *.grantthrive.com \
  --validation-method DNS \
  --region ap-southeast-2
```

#### 4.2 Route 53 DNS
```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name grantthrive.com \
  --caller-reference $(date +%s)

# Create A record pointing to load balancer
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "grantthrive.com",
        "Type": "A",
        "AliasTarget": {
          "DNSName": "[ALB_DNS_NAME]",
          "EvaluateTargetHealth": true,
          "HostedZoneId": "[ALB_ZONE_ID]"
        }
      }
    }]
  }'
```

### Step 5: Monitoring and Backup

#### 5.1 CloudWatch Monitoring
```bash
# Create CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "GrantThrive-HighCPU" \
  --alarm-description "High CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

#### 5.2 Database Backup
```bash
# Create automated backup
aws rds modify-db-instance \
  --db-instance-identifier grantthrive-prod \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00"
```

## 🔐 Security Configuration

### Environment Variables

Create `.env.production`:
```bash
# Database
DATABASE_URL=postgresql://grantthrive:[PASSWORD]@[RDS_ENDPOINT]:5432/grantthrive

# Security
JWT_SECRET_KEY=[SECURE_JWT_SECRET]
ENCRYPTION_KEY=[SECURE_ENCRYPTION_KEY]

# CORS
CORS_ORIGINS=https://grantthrive.com,https://www.grantthrive.com

# Email (if using SES)
AWS_SES_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=[SES_ACCESS_KEY]
AWS_SECRET_ACCESS_KEY=[SES_SECRET_KEY]

# File Storage
AWS_S3_BUCKET=grantthrive-documents
AWS_S3_REGION=ap-southeast-2

# Monitoring
SENTRY_DSN=[SENTRY_DSN_URL]
```

### Security Headers

Update nginx configuration:
```nginx
server {
    # ... existing configuration ...
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
}
```

## 📊 Health Checks and Monitoring

### Application Health Endpoint

The backend includes a health check endpoint at `/api/health`:

```python
@app.route('/api/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'database': check_database_connection(),
        'redis': check_redis_connection()
    }
```

### Monitoring Dashboard

Set up CloudWatch dashboard with:
- Application response times
- Error rates
- Database performance
- Server resource utilization
- User activity metrics

## 🔄 Deployment Pipeline

### CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-southeast-2
      
      - name: Build and push Docker images
        run: |
          # Build and push backend
          docker build -t grantthrive-backend ./backend
          docker tag grantthrive-backend:latest $ECR_REGISTRY/grantthrive-backend:latest
          docker push $ECR_REGISTRY/grantthrive-backend:latest
          
          # Build and push frontend
          docker build -t grantthrive-frontend ./frontend
          docker tag grantthrive-frontend:latest $ECR_REGISTRY/grantthrive-frontend:latest
          docker push $ECR_REGISTRY/grantthrive-frontend:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster grantthrive-cluster --service grantthrive-service --force-new-deployment
```

## 🚨 Disaster Recovery

### Backup Strategy
1. **Database**: Automated daily backups with 30-day retention
2. **Application**: Docker images stored in ECR
3. **Documents**: S3 with cross-region replication
4. **Configuration**: Infrastructure as Code with Terraform

### Recovery Procedures
1. **Database Recovery**: Point-in-time recovery from RDS snapshots
2. **Application Recovery**: Deploy from latest Docker images
3. **DNS Failover**: Route 53 health checks with automatic failover

## 📋 Post-Deployment Checklist

- [ ] SSL certificate installed and working
- [ ] DNS records pointing to load balancer
- [ ] Database connection successful
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Backup procedures tested
- [ ] Security scan completed
- [ ] Performance testing completed
- [ ] User acceptance testing completed

## 🤝 Support and Maintenance

### Regular Maintenance Tasks
- **Weekly**: Review monitoring alerts and performance metrics
- **Monthly**: Security updates and patches
- **Quarterly**: Backup testing and disaster recovery drills
- **Annually**: Security audit and penetration testing

### Support Contacts
- **Technical Support**: support@grantthrive.com
- **Emergency**: +61 XXX XXX XXX (24/7 on-call)
- **Documentation**: https://docs.grantthrive.com

---

For additional support or questions about deployment, contact the GrantThrive technical team at support@grantthrive.com.

