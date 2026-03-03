# GrantThrive Backend Platform

This repository contains the Flask-based backend API server for the GrantThrive ecosystem. It provides all data, authentication, and business logic for the five frontend applications.

---

## Local Development Setup

This guide covers how to install and run the backend API on your local machine. It has been tested on Ubuntu 22.04 with Python 3.11.

### Prerequisites

- **Python 3.11+**
- **Git**

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/BigLittleBusiness/grantthrive-platform.git
cd grantthrive-platform

# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all required Python packages
pip install -r requirements.txt

# Create the environment file from the example
cp .env.example .env
```

### 2. Configure Environment

Edit the `.env` file you just created:

- You **must** set a `SECRET_KEY`. You can generate one by running:
  `python -c "import secrets; print(secrets.token_hex(24))"`
- The default `DATABASE_URL` (`sqlite:///grantthrive_dev.db`) is fine for local use.
- The `MAIL_*` variables are optional. If you leave them blank, emails will be printed to your console instead of being sent.

### 3. Create Database

```bash
# Set the Flask app environment variable
export FLASK_ENV=development

# Create the database tables
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print(\'Database tables created successfully.\')"
```

### 4. Run the Server

```bash
# Run the Flask development server
flask run

# The API will now be running on http://localhost:5000
# You can verify it by visiting http://localhost:5000/api/health
```

### 5. (Optional) Seeding the Database

To populate your database with initial data (e.g., a system admin user, council tenants), you can use the seed scripts located in the `scripts/` directory.

```bash
# Example: Seed the database with initial councils and users
python3 scripts/seed_database.py
```
```
```
```
```
