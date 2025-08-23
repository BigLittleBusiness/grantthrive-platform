# GrantThrive Database Schema

This document outlines the database schema for the GrantThrive platform. The platform uses a relational database (SQLite for development, PostgreSQL for production) and the SQLAlchemy ORM for data access.

## 1. Tables

### 1.1. `users`

Stores user account information.

- `id` (Integer, Primary Key)
- `email` (String, Unique, Not Null)
- `password_hash` (String, Not Null)
- `first_name` (String)
- `last_name` (String)
- `council_name` (String)
- `role` (String, Not Null) - e.g., `council_admin`, `council_staff`, `community_user`
- `created_at` (DateTime)
- `updated_at` (DateTime)

### 1.2. `grants`

Stores information about grant programs.

- `id` (Integer, Primary Key)
- `title` (String, Not Null)
- `description` (Text)
- `amount` (Float)
- `category` (String)
- `status` (String) - e.g., `open`, `closed`, `archived`
- `council_id` (Integer, Foreign Key to `users.id`)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### 1.3. `applications`

Stores grant applications submitted by community users.

- `id` (Integer, Primary Key)
- `grant_id` (Integer, Foreign Key to `grants.id`)
- `user_id` (Integer, Foreign Key to `users.id`)
- `status` (String) - e.g., `draft`, `submitted`, `under_review`, `approved`, `rejected`
- `application_data` (JSON)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### 1.4. `audit_logs`

Stores a log of all significant actions taken on the platform.

- `id` (Integer, Primary Key)
- `user_id` (Integer, Foreign Key to `users.id`)
- `action` (String)
- `details` (Text)
- `timestamp` (DateTime)


