> **Note:** This document is a work-in-progress and provides a foundational guide for deploying the GrantThrive platform to AWS. It assumes a moderate level of familiarity with AWS services.

# GrantThrive AWS Deployment Guide

This guide provides a complete walkthrough for deploying the GrantThrive full-stack application to a production environment on Amazon Web Services. The architecture uses a scalable and cost-effective combination of services:

| Component | AWS Service | Purpose |
| :--- | :--- | :--- |
| **Database** | **RDS for PostgreSQL** | Managed, scalable, and reliable database. |
| **Backend API** | **EC2 + Gunicorn + Nginx** | Python application server running on a virtual machine. |
| **Frontend App** | **S3 + CloudFront** | Static site hosting with a global CDN for performance and SSL. |

---

## Architecture Diagram

```
+----------------+      +----------------+      +-----------------------+
|   End User     |----->|  CloudFront    |----->|      S3 Bucket        |
| (Browser)      |      | (app.your.com) |      | (React build files)   |
+----------------+      +----------------+      +-----------------------+
       |
       | API Calls
       v
+----------------+      +----------------+      +-----------------------+
|   Nginx on EC2 |----->| Gunicorn on EC2|----->|   RDS for PostgreSQL  |
| (api.your.com) |      | (Flask App)    |      | (Database)            |
+----------------+      +----------------+      +-----------------------+
```

---

## Part 1: Database Setup (AWS RDS)

The first step is to create a managed PostgreSQL database. The `README.md` file contains a detailed, step-by-step guide for this.

**Action:** Follow the instructions in **`README.md` -> Section 4 -> "Production Database (AWS RDS PostgreSQL)"**.

Once completed, you will have:
1.  An active RDS for PostgreSQL instance.
2.  Your database connection string (URL), which you should keep ready for the backend setup.

---

## Part 2: Backend Deployment (EC2 + Nginx)

Next, we will set up a virtual server to run the Flask backend API.

### Step 1: Launch an EC2 Instance

1.  Navigate to the [AWS EC2 Console](https://console.aws.amazon.com/ec2/).
2.  Click **Launch instance**.
3.  **Name:** `grantthrive-backend-server`.
4.  **AMI:** Select **Ubuntu**, version 22.04 LTS or higher.
5.  **Instance Type:** `t2.micro` or `t3.micro` is sufficient for a small-to-medium production load.
6.  **Key pair:** Create or select an existing key pair to enable SSH access.
7.  **Network settings:**
    *   Click **Edit**.
    *   Ensure the instance is in the same VPC as your RDS database.
    *   **Security group:** Create a new security group with the following inbound rules:
        *   `SSH` (TCP, port 22) from `My IP` (for your access).
        *   `HTTP` (TCP, port 80) from `Anywhere` (0.0.0.0/0).
        *   `HTTPS` (TCP, port 443) from `Anywhere` (0.0.0.0/0).
8.  Launch the instance.
9.  **Elastic IP:** Once the instance is running, create and associate an **Elastic IP** with it. This gives you a permanent public IP address for your server.

### Step 2: Configure the Server

Connect to your new EC2 instance via SSH using the key pair you selected.

```bash
ssh -i /path/to/your-key.pem ubuntu@<YOUR_ELASTIC_IP>
```

Now, install the necessary software:

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Git, Python, and Nginx
sudo apt install -y git python3.11 python3.11-venv nginx
```

### Step 3: Deploy the Application Code

Clone the backend repository and run the setup script.

```bash
# Clone the repository
git clone https://github.com/BigLittleBusiness/grantthrive-platform.git
cd grantthrive-platform

# Run the setup script (will create venv, install packages, create .env)
./setup.sh
```

Now, configure the environment for production:

1.  Edit the `.env` file: `nano .env`
2.  Set `FLASK_ENV=production`.
3.  Set `DATABASE_URL` to the connection string for your AWS RDS instance.
4.  Set `SERVER_NAME` to your backend's public domain (e.g., `api.grantthrive.com`).

Initialize the database schema on RDS:

```bash
# Activate the virtual environment
source venv/bin/activate

# Run the database migrations
flask db upgrade
```

### Step 4: Configure Gunicorn (Application Server)

Create a `systemd` service file to run Gunicorn as a background service.

```bash
sudo nano /etc/systemd/system/grantthrive.service
```

Paste the following configuration, updating the `User` and `WorkingDirectory` paths if necessary:

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

Start and enable the service:

```bash
sudo systemctl start grantthrive
sudo systemctl enable grantthrive
```

### Step 5: Configure Nginx (Reverse Proxy)

Create an Nginx configuration file.

```bash
sudo nano /etc/nginx/sites-available/grantthrive
```

Paste the following, replacing `api.yourdomain.com` with your actual backend domain:

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

Enable the site and restart Nginx:

```bash
# Link the config to sites-enabled
sudo ln -s /etc/nginx/sites-available/grantthrive /etc/nginx/sites-enabled

# Test for syntax errors
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

Finally, set up SSL using Certbot (Let's Encrypt) for HTTPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

Follow the prompts. Certbot will automatically obtain a certificate and configure Nginx to use it.

---

## Part 3: Frontend Deployment (S3 + CloudFront)

### Step 1: Build the Frontend for Production

On your **local machine**, navigate to the `grantthrive-frontend` directory.

1.  Create a production environment file: `cp .env.production.example .env.production`
2.  Edit `.env.production` and set `VITE_API_URL` to your backend API's public URL (e.g., `https://api.yourdomain.com/api`).
3.  Run the build command:

    ```bash
    pnpm install
    pnpm build
    ```

This will create a `dist` directory containing the optimized, static production files.

### Step 2: Create and Configure an S3 Bucket

1.  Navigate to the [AWS S3 Console](https://console.aws.amazon.com/s3/).
2.  **Create bucket**.
3.  **Bucket name:** `app.yourdomain.com` (using your domain name is a good convention).
4.  **Region:** Choose a region close to your users.
5.  **Block all public access:** Uncheck this box. You will need to acknowledge that the bucket will be public.
6.  Create the bucket.
7.  Go to the bucket's **Properties** tab and enable **Static website hosting**.
    *   **Index document:** `index.html`
    *   **Error document:** `index.html` (This is important for SPA routing).
8.  Go to the **Permissions** tab and apply a **Bucket Policy** to allow public read access. Click **Policy generator** to help create one, or use this template:

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::app.yourdomain.com/*"
            }
        ]
    }
    ```

### Step 3: Upload Files to S3

Upload the contents of your local `dist` directory to the S3 bucket you just created. You can do this via the AWS Console or the AWS CLI:

```bash
aws s3 sync ./dist s3://app.yourdomain.com
```

### Step 4: Create a CloudFront Distribution

1.  Navigate to the [AWS CloudFront Console](https://console.aws.amazon.com/cloudfront/).
2.  **Create distribution**.
3.  **Origin domain:** Select your S3 bucket from the dropdown.
4.  **Viewer protocol policy:** Select **Redirect HTTP to HTTPS**.
5.  **Alternate domain name (CNAME):** Enter your frontend domain (e.g., `app.yourdomain.com`).
6.  **Custom SSL certificate:** Select the SSL certificate for your domain (you can request one for free from AWS Certificate Manager).
7.  **Default root object:** Enter `index.html`.
8.  **Create distribution**.
9.  **Error Pages:** After the distribution is created, go to the **Error Pages** tab and create a **Custom Error Response**:
    *   **HTTP Error Code:** `403: Forbidden`
    *   **Customize Error Response:** `Yes`
    *   **Response Page Path:** `/index.html`
    *   **HTTP Response Code:** `200: OK`
    *   Create another one for `404: Not Found` with the same settings. This ensures all routes are handled by your React application.

---

## Part 4: DNS Configuration

Finally, update your domain's DNS records (e.g., in Amazon Route 53 or with your domain registrar).

1.  Create an **A record** for `api.yourdomain.com` that points to the **Elastic IP address** of your EC2 instance.
2.  Create an **A record** (or CNAME) for `app.yourdomain.com` that is an **Alias** to your **CloudFront distribution**.

After DNS propagation (which can take a few minutes to a few hours), your GrantThrive application will be live on AWS.
