> # GrantThrive: AWS RDS for PostgreSQL Setup Guide

This guide provides a detailed, step-by-step plan for creating and configuring a production-ready PostgreSQL database on AWS using the Relational Database Service (RDS). This database will serve as the backend for the GrantThrive platform.

---

## 1. Core Concepts: Why RDS?

Using a managed service like RDS instead of running a database on an EC2 instance offers significant advantages:

*   **Automated Management:** AWS handles patching, backups, and failover.
*   **Scalability:** You can easily scale the database instance size or storage with minimal downtime.
*   **High Availability:** RDS can be configured in a Multi-AZ (Availability Zone) deployment, which creates a standby replica in a different AZ for automatic failover.
*   **Security:** RDS provides robust security features, including encryption at rest and in transit, and integrates with AWS IAM and VPC.

---

## 2. Preparation: VPC and Security Groups

Before creating the database, you must have a Virtual Private Cloud (VPC) and a dedicated security group ready. This ensures your database is secure and only accessible by your application.

### Step 1: Create a Dedicated DB Security Group

1.  Navigate to the **VPC Dashboard** in the AWS Console.
2.  Go to **Security > Security Groups** and click **Create security group**.
3.  **Basic details:**
    *   **Security group name:** `grantthrive-db-sg`
    *   **Description:** `Allows inbound PostgreSQL traffic from the GrantThrive application server`
    *   **VPC:** Select the VPC where you will run your EC2 backend server.
4.  **Inbound rules:**
    *   Click **Add rule**.
    *   **Type:** `PostgreSQL` (This will automatically set the protocol to TCP and port to 5432).
    *   **Source:** This is the most critical step. Select **Custom** and choose the security group of your **EC2 application server** (e.g., `grantthrive-backend-sg`). **Do not** open the database to the public (`0.0.0.0/0`).
5.  Click **Create security group**.

> **Pro Tip:** By sourcing the rule from another security group, you create a secure link between your application and database layers without hardcoding IP addresses.

---

## 3. Creating the RDS Instance

Now, you will create the PostgreSQL database instance itself.

### Step 1: Launch the RDS Creation Wizard

1.  Navigate to the **RDS Dashboard** in the AWS Console.
2.  Click **Create database**.

### Step 2: Choose Creation Method and Engine

1.  **Choose a database creation method:** Select **Standard Create**.
2.  **Engine options:**
    *   **Engine type:** `PostgreSQL`
    *   **PostgreSQL version:** Select the latest available version (e.g., PostgreSQL 15.x or higher).

### Step 3: Select a Template

1.  **Templates:** Choose the template that matches your use case.
    *   **Production:** Provides defaults for high availability and performance. Use this for your live environment.
    *   **Dev/Test:** A less expensive configuration suitable for staging or testing.
    *   **Free tier:** Excellent for initial development and testing at no cost (if your account is eligible).

### Step 4: Configure Settings

1.  **DB instance identifier:** Give your database a unique name, e.g., `grantthrive-prod-db`.
2.  **Master credentials:**
    *   **Master username:** `grantthrive_admin` (or your preferred admin username).
    *   **Master password:** Enter a strong, secure password. Use a password manager to generate and store this.

### Step 5: Configure Instance and Storage

1.  **DB instance class:**
    *   For production, `db.t3.medium` or `db.t4g.medium` is a good starting point.
    *   For the free tier, `db.t3.micro` will be selected.
2.  **Storage:**
    *   **Storage type:** `General Purpose SSD (gp2)` is a good default.
    *   **Allocated storage:** Start with `20` GiB. You can scale this up later.
    *   **Enable storage autoscaling:** It is highly recommended to check this box to prevent your database from running out of space.

### Step 6: Configure Connectivity

This section is critical for ensuring your application can reach the database.

1.  **Virtual Private Cloud (VPC):** Select the same VPC where your EC2 backend server will reside.
2.  **DB Subnet Group:** It is best practice to place your database in private subnets. If you have a subnet group configured for this, select it. Otherwise, RDS can create one for you.
3.  **Public access:** Ensure this is set to **No**.
4.  **VPC security group (firewall):**
    *   Choose **Choose existing**.
    *   Select the `grantthrive-db-sg` security group you created earlier.
5.  **Database port:** Leave as `5432`.

### Step 7: Configure Database Authentication and Options

1.  **Database authentication:** `Password authentication` is sufficient.
2.  **Database options:**
    *   **Initial database name:** `grantthrive_prod` (This creates a specific database inside the instance, which is cleaner than using the default `postgres` database).
3.  **Backup:**
    *   **Enable automatic backups:** This should be enabled by default for production. Set a suitable retention period (e.g., 7 days).
4.  **Encryption:**
    *   **Enable encryption:** This should be enabled by default. It encrypts your data at rest.
5.  **Monitoring and Maintenance:**
    *   Leave the defaults unless you have specific requirements.

### Step 8: Create the Database

Review all your settings on the summary page, then click **Create database**. The process can take 10-15 minutes.

---

## 4. Connecting to the Database

Once the database status is **Available**, you can retrieve the connection details.

1.  Click on your new database instance in the RDS console.
2.  Go to the **Connectivity & security** tab.
3.  Note the **Endpoint** and **Port**.

Your full database connection URL (the `DATABASE_URL` for your `.env` file) will be in the following format:

```
postgresql://<YOUR_DB_USER>:<YOUR_DB_PASSWORD>@<YOUR_RDS_ENDPOINT>:<YOUR_RDS_PORT>/<YOUR_DB_NAME>
```

**Example:**

```
postgresql://grantthrive_admin:YourSecurePassword@grantthrive-prod-db.random-chars.ap-southeast-2.rds.amazonaws.com:5432/grantthrive_prod
```

This URL is what you will use to configure the backend Flask application, allowing it to connect to your new, production-ready database.
"))_AWS_SETUP.md", text = "> **Note:** This document is a work-in-progress and provides a foundational guide for deploying the GrantThrive platform to AWS. It assumes a moderate level of familiarity with AWS services.

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

**Action:** Follow the instructions in **`README.md` -> Section 4 -> \"Production Database (AWS RDS PostgreSQL)\"**.

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
Environment=\"PATH=/home/ubuntu/grantthrive-platform/venv/bin\"
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
        \"Version\": \"2012-10-17\",
        \"Statement\": [
            {
                \"Sid\": \"PublicReadGetObject\",
                \"Effect\": \"Allow\",
                \"Principal\": \"*\",
                \"Action\": \"s3:GetObject\",
                \"Resource\": \"arn:aws:s3:::app.yourdomain.com/*\"
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
"))" />
