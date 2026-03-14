# GrantThrive Developer Setup Guide

This guide provides comprehensive instructions for setting up, running, and deploying the GrantThrive platform. It covers running the frontend and backend together for local development, configuring a local database, and setting up a production database on AWS.

---

## 1. Project Architecture Overview

The GrantThrive platform consists of two primary components:

*   **Backend (`grantthrive-platform`):** A robust API server built with **Flask** (Python). It handles all business logic, user authentication, and database interactions.
*   **Frontend (`grantthrive-frontend`):** A modern single-page application built with **React** and **Vite**. It contains all the user interfaces, including the main council portal and public-facing pages.

These two projects are designed to run concurrently and communicate with each other. The frontend development server uses a proxy to forward all API requests to the backend server.

---

## 2. Prerequisites

Before you begin, ensure you have the following tools installed on your system:

| Tool | Minimum Version | Installation Command |
| :--- | :--- | :--- |
| Git | 2.34+ | `sudo apt install git` |
| Python | 3.11+ | `sudo apt install python3.11` |
| Node.js | 22.0+ | `nvm install 22` or from official site |
| pnpm | 10.0+ | `npm install -g pnpm` |

---

## 3. Local Development Setup

This section guides you through running both the frontend and backend on your local machine. The backend will run on `http://localhost:5000` and the frontend on `http://localhost:5173`.

### Step 1: Clone the Repositories

First, clone both the backend and frontend repositories into a single parent directory.

```bash
# Create a main project directory
mkdir grantthrive-project
cd grantthrive-project

# Clone the backend platform
git clone https://github.com/BigLittleBusiness/grantthrive-platform.git

# Clone the frontend application
git clone https://github.com/BigLittleBusiness/GrantThrive-frontend.git
```

### Step 2: Set Up and Run the Backend

The backend repository includes an automated setup script that handles nearly everything.

```bash
# Navigate into the backend directory
cd grantthrive-platform

# Make the setup script executable
chmod +x setup.sh

# Run the automated setup
./setup.sh
```

This script will:
1.  Create a Python virtual environment (`venv`).
2.  Install all required Python dependencies.
3.  Create a `.env` file from the example and generate a secure `SECRET_KEY`.
4.  Initialize the local SQLite database (`instance/grantthrive_dev.db`).

Once the setup is complete, start the backend server:

```bash
# Activate the virtual environment
source venv/bin/activate

# Start the Flask development server
flask run

# The backend API is now running at http://localhost:5000
# You can verify it by opening http://localhost:5000/api/health in your browser.
```

### Step 3: Set Up and Run the Frontend

In a **new terminal window**, navigate to the frontend directory and install the dependencies using `pnpm`.

```bash
# Navigate into the frontend directory (from the parent grantthrive-project directory)
cd ../grantthrive-frontend

# Install all Node.js dependencies
pnpm install
```

This command installs all packages for the frontend application. The project is already configured to proxy API requests to the backend running on port 5000.

Now, start the frontend development server:

```bash
# Start the Vite development server
pnpm dev

# The frontend is now running at http://localhost:5173
```

You can now access the full GrantThrive application in your browser at `http://localhost:5173`. Any API calls the frontend makes will be automatically routed to your local backend server.

---

## 4. Database Configuration

### Local Database (SQLite)

For local development, the project is pre-configured to use **SQLite**, a simple file-based database. The `setup.sh` script automatically creates the database file at `grantthrive-platform/instance/grantthrive_dev.db`.

*   **No further setup is required for local development.**
*   To reset the database, simply delete the `instance/` directory and re-run `./setup.sh`.

### Production Database (AWS RDS PostgreSQL)

For a production environment on AWS, you should use a managed PostgreSQL database via **Amazon RDS**. The application is already equipped with the necessary driver (`psycopg2-binary`) to connect to PostgreSQL.

**Step 1: Create an AWS RDS for PostgreSQL Instance**

1.  Navigate to the [AWS RDS Console](https://console.aws.amazon.com/rds/).
2.  Click **Create database**.
3.  Choose **Standard Create** and select **PostgreSQL**.
4.  Select a version (e.g., PostgreSQL 15 or higher).
5.  Under **Templates**, choose **Free tier** for testing/staging, or select a suitable production instance size.
6.  Define a **DB instance identifier** (e.g., `grantthrive-prod-db`), a **master username** (e.g., `grantthrive_admin`), and a **master password**.
7.  **Crucially, under Connectivity:**
    *   Ensure the RDS instance is launched into the same VPC as your backend application server (e.g., your EC2 instance or ECS service).
    *   Configure the **VPC security group** to allow inbound traffic on **port 5432** from the security group of your application server. This is essential for the application to be able to connect to the database.
8.  Click **Create database**.

**Step 2: Configure the Backend**

Once your RDS instance is created and available, retrieve its connection details from the RDS console (the **Endpoint** and **Port**).

1.  Open the `.env` file in your `grantthrive-platform` directory on your production server.
2.  Locate the `DATABASE_URL` variable.
3.  Update it with your RDS PostgreSQL connection string, a new, more comprehensive versionreplacing the placeholders with your actual credentials:

    ```ini
    # .env
    # ... other variables

    # PostgreSQL connection string for AWS RDS
    DATABASE_URL="postgresql://<YOUR_DB_USER>:<YOUR_DB_PASSWORD>@<YOUR_RDS_ENDPOINT>:<YOUR_RDS_PORT>/<YOUR_DB_NAME>"

    # ... other variables
    ```

    *   `<YOUR_DB_USER>`: The master username you set (e.g., `grantthrive_admin`).
    *   `<YOUR_DB_PASSWORD>`: The master password you set.
    *   `<YOUR_RDS_ENDPOINT>`: The endpoint URL provided in the RDS console.
    *   `<YOUR_RDS_PORT>`: The port (usually 5432).
    *   `<YOUR_DB_NAME>`: The initial database name you set during creation (defaults to `postgres` if not specified, but it's best practice to create a dedicated database, e.g., `grantthrive_prod`).

**Step 3: Initialize the Production Database**

After configuring the `DATABASE_URL`, you need to create the tables in your new RDS database. Connect to your production server via SSH and run the following commands from the `grantthrive-platform` directory:

```bash
# Activate the virtual environment
source venv/bin/activate

# Set the environment to production
export FLASK_ENV=production

# Run the database migrations to create all tables
flask db upgrade

# You can optionally seed the database with initial data
# python3 scripts/seed_database.py
```

Your backend application is now configured to use the production AWS RDS database. When you restart the Flask application, it will connect to PostgreSQL instead of the local SQLite file.
