# Repository Secrets Configuration

This document outlines the required repository secrets that need to be configured in GitHub Settings > Secrets and variables > Actions.

## Required Secrets

### Deployment Secrets
- `STAGING_API_KEY`: API key for staging deployment
- `STAGING_URL`: URL for staging environment
- `PRODUCTION_API_KEY`: API key for production deployment (when ready)
- `PRODUCTION_URL`: URL for production environment (when ready)

### Database Secrets
- `DATABASE_URL`: Database connection string for testing and deployment
- `DATABASE_URL_STAGING`: Database connection string for staging environment
- `DATABASE_URL_PRODUCTION`: Database connection string for production environment

### Security Secrets
- `JWT_SECRET`: Secret key for JWT token generation (32+ characters)
- `JWT_REFRESH_SECRET`: Secret key for JWT refresh tokens (32+ characters)
- `ENCRYPTION_KEY`: Key for encrypting sensitive data

### Email Service Secrets
- `EMAIL_API_KEY`: API key for email service (SendGrid, AWS SES, etc.)
- `EMAIL_FROM_ADDRESS`: Sender email address for system emails
- `EMAIL_SERVICE_URL`: Email service endpoint (if applicable)

### External Service Secrets
- `AWS_ACCESS_KEY_ID`: AWS access key for S3 storage
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for S3 storage
- `AWS_REGION`: AWS region for services
- `S3_BUCKET_NAME`: S3 bucket name for file storage

## Environment Variables

### Development Environment
- `NODE_ENV`: Set to "development" for development builds
- `API_BASE_URL`: Base URL for API endpoints (e.g., http://localhost:8000)
- `FRONTEND_URL`: Base URL for frontend application (e.g., http://localhost:3000)
- `DATABASE_URL`: Local database connection string

### Staging Environment
- `NODE_ENV`: Set to "staging"
- `API_BASE_URL`: Staging API URL
- `FRONTEND_URL`: Staging frontend URL
- `DATABASE_URL`: Staging database connection string

### Production Environment
- `NODE_ENV`: Set to "production"
- `API_BASE_URL`: Production API URL
- `FRONTEND_URL`: Production frontend URL
- `DATABASE_URL`: Production database connection string

## Security Notes

1. **Never commit secrets to the repository**
2. **Use strong, unique secrets for each environment**
3. **Rotate secrets regularly**
4. **Limit access to secrets to necessary team members only**
5. **Use environment-specific secrets for different deployment stages**

## Setup Instructions

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with the exact name and value
5. Ensure all secrets are properly configured before running CI/CD pipelines

## Validation

After setting up secrets, you can validate them by:
1. Running a test workflow that uses the secrets
2. Checking that environment variables are properly passed to the application
3. Verifying that sensitive operations (authentication, database connections) work correctly 