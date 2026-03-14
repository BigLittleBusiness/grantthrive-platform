> # GrantThrive: AWS EC2 Backend Deployment Guide

This guide provides a detailed, step-by-step plan for deploying the GrantThrive Flask backend API to a production environment on an AWS EC2 instance. It covers server setup, application deployment, and configuration of Gunicorn and Nginx for a robust, scalable setup.

---

## 1. Prerequisites

Before you begin, you must have:

1.  **An AWS Account** with appropriate permissions to create EC2 instances and related resources.
2.  **An AWS RDS for PostgreSQL Instance** already created and available, as detailed in the `AWS_RDS_SETUP.md` guide. You will need the database connection string.
3.  **A Domain Name** that you can manage DNS for. The backend will be hosted on a subdomain (e.g., `api.yourdomain.com`).
4.  **An SSH Key Pair** for securely connecting to your EC2 instance.

---

## 2. Launching the EC2 Instance

First, create the virtual server that will host the application.

### Step 1: Navigate to the EC2 Console

1.  Open the [AWS EC2 Console](https://console.aws.amazon.com/ec2/).
2.  Click **Launch instance**.

### Step 2: Configure Instance Details

1.  **Name:** `grantthrive-backend-server`
2.  **Application and OS Images (AMI):** Select **Ubuntu**, and choose the latest LTS version (e.g., **Ubuntu Server 22.04 LTS**).
3.  **Instance type:** `t2.micro` or `t3.micro` is a cost-effective choice for a small-to-medium production environment.
4.  **Key pair (login):** Select the SSH key pair you will use to access the instance.

### Step 3: Configure Network Settings

This is a critical step to ensure your server is secure and can communicate with your database.

1.  Click **Edit** next to Network settings.
2.  **VPC:** Select the same VPC where your RDS database is located.
3.  **Security group:**
    *   Click **Create security group**.
    *   **Security group name:** `grantthrive-backend-sg`
    *   **Description:** `Allows web and SSH traffic for the GrantThrive backend`
    *   **Inbound security groups rules:**
        *   **Rule 1:**
            *   **Type:** `SSH`
            *   **Source type:** `My IP` (This restricts SSH access to your current IP address for security).
        *   **Rule 2:**
            *   **Type:** `HTTP`
            *   **Source type:** `Anywhere`.
        *   **Rule 3:**
            *   **Type:** `HTTPS`
            *   **Source type:** `Anywhere`.
4.  Review the remaining settings and click **Launch instance**.

### Step 4: Associate an Elastic IP

An Elastic IP provides a permanent public IP address for your server.

1.  In the EC2 console, go to **Elastic IPs**.
2.  Click **Allocate Elastic IP address**.
3.  Once allocated, select it and choose **Actions > Associate Elastic IP address**.
4.  Select your `grantthrive-backend-server` instance and click **Associate**.

---

## 3. Server Configuration and Application Deployment

Now, connect to your server and deploy the application code.

### Step 1: Connect to the Instance

Use your SSH key to connect to the server with the Elastic IP you just associated.

```bash
ssh -i /path/to/your-key.pem ubuntu@<YOUR_ELASTIC_IP>
```

### Step 2: Install Server Dependencies

Install Git for code cloning, Python for running the app, and Nginx as the web server.

```bash
# Update all system packages
sudo apt update && sudo apt upgrade -y

# Install required software
sudo apt install -y git python3.11 python3.11-venv nginx
```

### Step 3: Deploy the Application

Clone the repository and run the included setup script.

```bash
# Clone the backend code
git clone https://github.com/BigLittleBusiness/grantthrive-platform.git
cd grantthrive-platform

# Run the automated setup script
./setup.sh
```

### Step 4: Configure for Production

Edit the `.env` file to configure it for your production environment.

```bash
nano .env
```

Make the following changes:

1.  **`FLASK_ENV`**: Set to `production`.
2.  **`DATABASE_URL`**: Paste the full connection string for your AWS RDS PostgreSQL database.
3.  **`SERVER_NAME`**: Set to your backend's public domain (e.g., `api.yourdomain.com`).

### Step 5: Initialize the Production Database

Run the database migrations to create the schema in your RDS instance.

```bash
# Activate the virtual environment
source venv/bin/activate

# Apply the database migrations
flask db upgrade
```

---

## 4. Gunicorn and Nginx Configuration

Instead of using the Flask development server, we will use Gunicorn as a robust application server and Nginx as a reverse proxy.

### Step 1: Configure Gunicorn as a Systemd Service

Creating a `systemd` service ensures Gunicorn runs automatically in the background and restarts on failure.

```bash
sudo nano /etc/systemd/system/grantthrive.service
```

Paste in the following service definition:

```ini
[Unit]
Description=Gunicorn instance to serve GrantThrive
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/grantthrive-platform
Environment="PATH=/home/ubuntu/grantthrive-platform/venv/bin"
ExecStart=/home/ubuntu/grantthrive-platform/venv/bin/gunicorn --workers 3 --bind unix:grantthrive.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

> **Note:** This configuration uses a Unix socket (`grantthrive.sock`) for efficient communication between Nginx and Gunicorn.

Now, start and enable the service:

```bash
sudo systemctl start grantthrive
sudo systemctl enable grantthrive

# Check the status to ensure it's running without errors
sudo systemctl status grantthrive
```

### Step 2: Configure Nginx as a Reverse Proxy

Nginx will handle incoming web traffic and forward it to Gunicorn.

```bash
sudo nano /etc/nginx/sites-available/grantthrive
```

Paste in the following server block, replacing `api.yourdomain.com` with your domain:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/grantthrive-platform/grantthrive.sock;
    }
}
```

Enable this configuration and restart Nginx:

```bash
# Create a symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/grantthrive /etc/nginx/sites-enabled

# Remove the default Nginx welcome page if it exists
sudo rm /etc/nginx/sites-enabled/default

# Test the Nginx configuration for syntax errors
sudo nginx -t

# Restart Nginx to apply the changes
sudo systemctl restart nginx
```

At this point, your backend should be accessible via HTTP at `http://api.yourdomain.com`.

---

## 5. Securing with SSL (HTTPS)

Finally, secure your API with a free SSL certificate from Let's Encrypt using Certbot.

### Step 1: Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Step 2: Obtain and Install the Certificate

Run Certbot, which will automatically edit your Nginx configuration to enable HTTPS.

```bash
sudo certbot --nginx -d api.yourdomain.com
```

Follow the on-screen prompts. Choose the option to **redirect HTTP traffic to HTTPS**.

Certbot will also set up a cron job to automatically renew the certificate before it expires.

Your GrantThrive backend is now fully deployed, secure, and running at `https://api.yourdomain.com`.
