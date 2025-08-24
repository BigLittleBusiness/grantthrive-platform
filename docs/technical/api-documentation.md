# GrantThrive API Documentation

This document provides a detailed overview of the GrantThrive API. The API is designed to be RESTful and uses JSON for all requests and responses.

## 1. Authentication

All API requests must be authenticated using a JSON Web Token (JWT). The token must be included in the `Authorization` header of each request, with the `Bearer` scheme.

`Authorization: Bearer <your_jwt>`

### 1.1. Register

- **Endpoint:** `POST /api/auth/register`
- **Description:** Creates a new user account.
- **Request Body:**
  ```json
  {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "password": "your_password"
  }
  ```
- **Response:**
  ```json
  {
    "message": "User created successfully."
  }
  ```

### 1.2. Login

- **Endpoint:** `POST /api/auth/login`
- **Description:** Authenticates a user and returns a JWT.
- **Request Body:**
  ```json
  {
    "email": "john.doe@example.com",
    "password": "your_password"
  }
  ```
- **Response:**
  ```json
  {
    "access_token": "your_jwt"
  }
  ```

## 2. Grants

### 2.1. List Grants

- **Endpoint:** `GET /api/grants`
- **Description:** Returns a list of all grants.
- **Response:**
  ```json
  [
    {
      "id": 1,
      "title": "Community Garden Grant",
      "description": "A grant to support community gardens.",
      "amount": 5000
    }
  ]
  ```

### 2.2. Get Grant

- **Endpoint:** `GET /api/grants/<id>`
- **Description:** Returns a single grant by ID.
- **Response:**
  ```json
  {
    "id": 1,
    "title": "Community Garden Grant",
    "description": "A grant to support community gardens.",
    "amount": 5000
  }
  ```

### 2.3. Create Grant

- **Endpoint:** `POST /api/grants`
- **Description:** Creates a new grant. (Council Administrators only)
- **Request Body:**
  ```json
  {
    "title": "New Grant",
    "description": "A new grant program.",
    "amount": 10000
  }
  ```
- **Response:**
  ```json
  {
    "message": "Grant created successfully."
  }
  ```

## 3. Applications

### 3.1. List Applications

- **Endpoint:** `GET /api/applications`
- **Description:** Returns a list of all applications for the authenticated user.
- **Response:**
  ```json
  [
    {
      "id": 1,
      "grant_id": 1,
      "status": "Submitted"
    }
  ]
  ```

### 3.2. Get Application

- **Endpoint:** `GET /api/applications/<id>`
- **Description:** Returns a single application by ID.
- **Response:**
  ```json
  {
    "id": 1,
    "grant_id": 1,
    "status": "Submitted"
  }
  ```

### 3.3. Create Application

- **Endpoint:** `POST /api/applications`
- **Description:** Creates a new application for a grant.
- **Request Body:**
  ```json
  {
    "grant_id": 1,
    "answers": {
      "question_1": "Our project aims to..."
    }
  }
  ```
- **Response:**
  ```json
  {
    "message": "Application submitted successfully."
  }
  ```


