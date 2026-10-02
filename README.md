# GrantThrive Developer Setup Guide

This guide provides comprehensive instructions for setting up, running, and deploying the GrantThrive platform. It covers running the frontend and backend together for local development, configuring a local database, and setting up a production database on AWS.

---

## 1. Project Architecture Overview

The GrantThrive platform consists of two primary components:

*   **Backend (`grantthrive-platform`):** A robust API server built with **Flask** (Python). It handles all business logic, user authentication, and database interactions.
*   **Frontend (`grantthrive-frontend`):** A modern single-page application built with **React** and **Vite**. It contains all the user interfaces, including the main council portal and public-facing pages.

These two projects are designed to run concurrently and communicate with each other. Every backend endpoint is served under `/api`; the frontend calls the backend directly at `VITE_API_URL` (which includes `/api`).

---

## 2. Prerequisites

Before you begin, ensure you have the following tools installed on your system:

| Tool | Minimum Version | Installation Command |
| :--- | :--- | :--- |
| Git | 2.34+ | `sudo apt install git` |
| Python | 3.11 or 3.12 (newer versions lack wheels for pinned dependencies) | `sudo apt install python3.11` |
| PostgreSQL | 15+ | `sudo apt install postgresql` |
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
4.  Apply the database migrations to the PostgreSQL database in `DATABASE_URL` (see section 4).

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

Copy `.env.example` to `.env`; its `VITE_API_URL=http://localhost:5000/api` points the frontend at this backend. Then start the frontend development server:

```bash
# Start the Vite development server
pnpm dev

# The frontend is now running at http://localhost:5173
```

You can now access the full GrantThrive application in your browser at `http://localhost:5173`. The frontend calls the backend directly at `VITE_API_URL`; the backend's default `CORS_ORIGINS` already allow `http://localhost:5173`.

Every backend endpoint lives under `/api`. In production a single domain can serve both: route `/api/*` to the backend and everything else to the built frontend (see `scripts/aws_setup.sh` for the Nginx configuration), and build the frontend with `VITE_API_URL=/api`.

---

## 4. Database Configuration

### Local Database (PostgreSQL)

GrantThrive requires **PostgreSQL** in every environment (SQLite is not supported). Create a local database and point `DATABASE_URL` in `.env` at it before running `./setup.sh`:

```bash
createdb grantthrive_dev
# .env
DATABASE_URL="postgresql://<user>:<password>@localhost:5432/grantthrive_dev"
```

*   `./setup.sh` (or `flask db upgrade`) applies all migrations.
*   To reset the database, drop and recreate it, then run `flask db upgrade` again.

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

```

Your backend application is now configured to use the production AWS RDS database. When you restart the Flask application, it will connect to the RDS database.

---

## 5. Billing (Stripe Subscriptions)

Councils pay for GrantThrive with a Stripe subscription. Customers with an Australian billing address are charged **10% GST on top** of the plan price (via Stripe Tax); overseas customers are not charged GST. All charges are in AUD.

### How it works

1.  **Registration** — a council must choose a plan (`small` / `medium` / `large`) and a billing cycle (`monthly` / `annual`). The choice is stored on the pending user.
2.  **Approval** — when a system admin approves the registration, the council is created on trial limits and the chosen plan is copied to it. Nobody is charged before approval.
3.  **Checkout** — the council admin subscribes from **Account & Billing** (their plan is pre-selected). The backend creates a Stripe Checkout session; Stripe collects the card, billing address (which determines GST) and optional ABN.
4.  **Activation** — the subscription is applied to the council (its `plan` switches from `trial` to the subscribed plan) both when the user returns from Checkout and via the webhook.
5.  **Management** — "Manage billing" opens the Stripe Customer Portal (card, invoices, plan change, cancellation). Renewals, failed payments and cancellations reach the app through the webhook.

| Subscription status | Council entitlements |
| :--- | :--- |
| `active`, `trialing`, `past_due` | The subscribed plan |
| `canceled`, `unpaid`, `incomplete_expired` | Trial limits |

### API (`/api/billing`)

| Endpoint | Who | Purpose |
| :--- | :--- | :--- |
| `GET /plans` | Public | Plan prices from Stripe (ex-GST) with each plan's limits |
| `POST /checkout-session` | Council admin | Start Checkout `{ plan, billing_cycle }` → `{ url }` |
| `POST /checkout-session/sync` | Council admin | Apply a completed checkout on return `{ session_id }` |
| `POST /portal-session` | Council admin | Open the Customer Portal → `{ url }` |
| `POST /webhook` | Stripe | Signed webhook events |

The council's subscription state is also returned in `GET /api/councils/<id>/billing` (`subscription` block).

### One-time Stripe account setup

Requires **Stripe Tax** to be active with an Australian registration (Stripe Dashboard → Tax). Then run:

```bash
STRIPE_SECRET_KEY=sk_test_... python scripts/stripe_setup.py
```

The script is idempotent. It finds the six "GrantThrive <Plan> - Monthly/Yearly" prices, gives them lookup keys (`grantthrive_<plan>_<monthly|annual>`), marks them **tax-exclusive** (so GST is added on top), sets the SaaS tax code, creates a GrantThrive Customer Portal configuration and prints `STRIPE_PORTAL_CONFIGURATION_ID`. Run it once per Stripe account (test and live).

> Prices are always charged from Stripe. To change a price, create a new price in Stripe and move the lookup key to it (re-running the script handles this for matching product names). The admin "Pricing Management" screen only changes prices displayed in the app.

### Environment variables

| Variable | Description |
| :--- | :--- |
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_test_…` / `sk_live_…`). Never commit it. |
| `STRIPE_WEBHOOK_SECRET` | Signing secret of the webhook endpoint (`whsec_…`). |
| `STRIPE_PORTAL_CONFIGURATION_ID` | Printed by `scripts/stripe_setup.py` (`bpc_…`). |
| `APP_URL` | Public frontend URL; Checkout and the portal redirect back here (e.g. `https://app.grantthrive.com`). |

The frontend needs no Stripe keys — it redirects to Stripe-hosted pages.

### Webhook

In the Stripe Dashboard → **Developers → Webhooks → Add endpoint**:

*   **Endpoint URL:** `https://<your API host>/api/billing/webhook`
*   **Events to send:**

| Event | Why |
| :--- | :--- |
| `checkout.session.completed` | A council finished Checkout — activate the subscription |
| `customer.subscription.created` | Subscription created |
| `customer.subscription.updated` | Plan change, renewal, `past_due`, cancel-at-period-end |
| `customer.subscription.deleted` | Subscription ended — council returns to trial limits |
| `customer.subscription.paused` | Subscription paused |
| `customer.subscription.resumed` | Subscription resumed |
| `invoice.paid` | Renewal paid — refresh status and period end |
| `invoice.payment_failed` | Payment failed — status becomes `past_due` |

Copy the endpoint's **Signing secret** into `STRIPE_WEBHOOK_SECRET`. Use a separate endpoint (and secret) for test mode and live mode.

For local development, use the [Stripe CLI](https://docs.stripe.com/stripe-cli):

```bash
stripe listen --forward-to localhost:5000/api/billing/webhook
# copy the printed whsec_... into STRIPE_WEBHOOK_SECRET and restart the backend
```

Without a webhook, a payment is still confirmed when the user returns from Checkout, but renewals, failed payments and cancellations made in Stripe will not reach the app.

### Testing

Use Stripe test mode with card `4242 4242 4242 4242`, any future expiry and any CVC. An Australian billing address shows `GST (10%)` at checkout; other countries show no GST.
