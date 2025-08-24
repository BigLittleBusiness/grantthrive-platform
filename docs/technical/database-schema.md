# GrantThrive Database Schema

This document outlines the database schema for the GrantThrive platform. The schema is designed to be flexible and scalable to support the needs of councils, philanthropic organisations, and community members.

## 1. Tables

### 1.1. `users`

Stores user accounts.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary Key |
| `name` | VARCHAR | User's full name |
| `email` | VARCHAR | User's email address (must be unique) |
| `password_hash` | VARCHAR | Hashed password |
| `role` | VARCHAR | User's role (`council_admin`, `council_staff`, `community`) |
| `council_id` | INTEGER | Foreign key to `councils` table (for council users) |
| `created_at` | DATETIME | Timestamp of when the user was created |

### 1.2. `councils`

Stores council information.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary Key |
| `name` | VARCHAR | Council's name |
| `subdomain` | VARCHAR | Unique subdomain for the council's GrantThrive portal |
| `created_at` | DATETIME | Timestamp of when the council was created |

### 1.3. `grants`

Stores grant programs.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary Key |
| `council_id` | INTEGER | Foreign key to `councils` table |
| `title` | VARCHAR | Grant title |
| `description` | TEXT | Grant description |
| `amount` | INTEGER | Funding amount |
| `status` | VARCHAR | Grant status (`draft`, `open`, `closed`, `archived`) |
| `application_open_date` | DATETIME | Date when applications open |
| `application_close_date` | DATETIME | Date when applications close |
| `created_at` | DATETIME | Timestamp of when the grant was created |

### 1.4. `applications`

Stores grant applications.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary Key |
| `grant_id` | INTEGER | Foreign key to `grants` table |
| `user_id` | INTEGER | Foreign key to `users` table |
| `status` | VARCHAR | Application status (`draft`, `submitted`, `under_review`, `approved`, `rejected`) |
| `answers` | JSON | Applicant's answers to the application form questions |
| `created_at` | DATETIME | Timestamp of when the application was created |
| `submitted_at` | DATETIME | Timestamp of when the application was submitted |

### 1.5. `application_reviews`

Stores reviews of grant applications.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary Key |
| `application_id` | INTEGER | Foreign key to `applications` table |
| `reviewer_id` | INTEGER | Foreign key to `users` table (council staff) |
| `recommendation` | VARCHAR | Reviewer's recommendation (`approve`, `reject`) |
| `comments` | TEXT | Reviewer's comments |
| `created_at` | DATETIME | Timestamp of when the review was created |

## 2. Relationships

- A `council` has many `users`.
- A `council` has many `grants`.
- A `user` can have one `council` (if they are a council user).
- A `grant` belongs to one `council`.
- A `grant` has many `applications`.
- An `application` belongs to one `grant`.
- An `application` belongs to one `user`.
- An `application` has many `application_reviews`.
- An `application_review` belongs to one `application`.
- An `application_review` belongs to one `user` (the reviewer).


