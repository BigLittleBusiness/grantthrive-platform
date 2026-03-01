# GrantThrive Backend Platform

This repository contains the Flask-based backend API server for the GrantThrive ecosystem. It provides all data, authentication, and business logic for the five frontend applications.

---

## Local Development Setup

This guide covers how to install and run the backend API on your local machine.

### Prerequisites

- **Python 3.11+**
- **Git**

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/BigLittleBusiness/grantthrive-platform.git
cd grantthrive-platform

# Create a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all required Python packages
pip install -r requirements.txt

# Create the environment file
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
export FLASK_APP=manage.py

# Create the database tables
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

### 4. Run the Server

```bash
# Run the Flask development server
flask run

# The API will now be running on http://localhost:5000
```
