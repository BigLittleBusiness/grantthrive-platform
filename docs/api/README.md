# GrantThrive API Documentation

## API Overview

The GrantThrive Platform provides a comprehensive RESTful API for grant management, user authentication, and community features.

## Base URL
- **Development**: `http://localhost:8000`
- **Staging**: `https://api-staging.grantthrive.com`
- **Production**: `https://api.grantthrive.com`

## Authentication

### JWT Token Authentication
All API endpoints require authentication using JWT tokens.

```bash
# Login to get access token
POST /auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# Use token in Authorization header
Authorization: Bearer <access_token>
```

## Core Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - User logout
- `POST /auth/verify-email` - Email verification
- `POST /auth/forgot-password` - Password reset request
- `POST /auth/reset-password` - Password reset

### Grant Management
- `GET /grants` - List grant programs
- `POST /grants` - Create grant program
- `GET /grants/{id}` - Get grant program details
- `PUT /grants/{id}` - Update grant program
- `DELETE /grants/{id}` - Delete grant program

### Applications
- `GET /applications` - List applications
- `POST /applications` - Submit application
- `GET /applications/{id}` - Get application details
- `PUT /applications/{id}` - Update application
- `DELETE /applications/{id}` - Withdraw application

### Community
- `GET /forums` - List forum discussions
- `POST /forums` - Create discussion
- `GET /resources` - List resources
- `POST /resources` - Upload resource

## Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Success message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Handling

Error responses include detailed information:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "field": "error message"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Rate Limiting

API requests are rate-limited:
- **Authenticated users**: 1000 requests per hour
- **Unauthenticated users**: 100 requests per hour

## Documentation

- **Interactive API Docs**: Available at `/docs` when running locally
- **OpenAPI Specification**: Available at `/openapi.json`
- **Postman Collection**: Available for import 