# GrantThrive API Documentation

This document provides a detailed overview of the GrantThrive RESTful API. It is intended for developers who need to integrate with the platform or understand its architecture.

## 1. Authentication

The GrantThrive API uses JSON Web Tokens (JWT) for authentication. All API requests (except for the `/api/auth/login` and `/api/auth/register` endpoints) must include a valid JWT in the `Authorization` header as a Bearer token.

`Authorization: Bearer <your_jwt>`

## 2. API Endpoints

The following sections detail the available API endpoints.

### 2.1. Authentication (`/api/auth`)

- `POST /register`: Register a new user.
- `POST /login`: Authenticate a user and receive a JWT.
- `POST /verify`: Verify a JWT.
- `POST /refresh`: Refresh an expired JWT.
- `POST /change-password`: Change a user's password.
- `POST /forgot-password`: Initiate the password reset process.

### 2.2. Grants (`/api/grants`)

- `GET /`: Get a list of all grants.
- `GET /<id>`: Get a specific grant by its ID.
- `POST /`: Create a new grant (council users only).
- `PUT /<id>`: Update an existing grant.
- `DELETE /<id>`: Delete a grant.
- `GET /categories`: Get a list of available grant categories.
- `GET /public`: Get a list of public grants (no authentication required).

### 2.3. Applications (`/api/applications`)

- `GET /`: Get a list of all applications.
- `GET /<id>`: Get a specific application by its ID.
- `POST /`: Submit a new application.
- `PUT /<id>/status`: Update the status of an application (council users only).
- `PUT /<id>`: Update an existing application.
- `DELETE /<id>`: Delete or withdraw an application.
- `GET /stats`: Get application statistics (council users only).

### 2.4. Analytics (`/api/analytics`)

- `GET /overview`: Get an overview of platform analytics.
- `GET /trends`: Get trend data for grants and applications.
- `GET /distribution`: Get data on the distribution of grants by category.
- `GET /performance`: Get performance metrics for the platform.


