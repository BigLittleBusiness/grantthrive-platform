# GrantThrive API Documentation

## Overview

The GrantThrive API provides comprehensive access to all platform functionality through RESTful endpoints. The API is designed to support both the web application and potential third-party integrations.

## Authentication

All API endpoints require authentication using JWT tokens:

```http
Authorization: Bearer <jwt_token>
```

## Core Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/logout` - User logout

### Grant Management
- `GET /api/grants` - List available grants
- `POST /api/grants` - Create new grant program
- `GET /api/grants/{id}` - Get grant details
- `POST /api/applications` - Submit grant application
- `GET /api/applications` - List user applications

### Community Features
- `GET /api/forums` - List discussion forums
- `POST /api/forums/{id}/posts` - Create forum post
- `GET /api/resources` - List resource library items
- `POST /api/resources` - Upload new resource

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

```json
{
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  }
}
``` 