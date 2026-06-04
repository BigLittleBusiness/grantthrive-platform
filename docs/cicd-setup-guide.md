# GrantThrive CI/CD Setup Guide

This legacy EC2 CI/CD guide is retained for historical reference. The active AWS workflows deploy UAT from the `staging` branch and production from the `prod` branch.

---

## 1. AWS Server Setup (One-Time)

First, you must prepare your EC2 server to receive deployments. The `aws_setup.sh` script automates this entire process.

1.  **Copy the script to your server:**

    ```bash
    # From your local machine
    scp scripts/aws_setup.sh ubuntu@<your-ec2-ip>:/home/ubuntu/
    ```

2.  **SSH into your server and run the script:**

    ```bash
    ssh ubuntu@<your-ec2-ip>
    chmod +x aws_setup.sh
    sudo ./aws_setup.sh
    ```

    This script installs all required packages (Nginx, Python, etc.), configures the directory structure (`/srv/grantthrive` and `/var/www/grantthrive`), and sets up the `grantthrive-backend` systemd service.

---

## 2. GitHub Secrets Configuration

This is the most critical step. You must add the following secrets to the GitHub repository settings for **both** repositories. Go to `Settings` → `Secrets and variables` → `Actions` and click `New repository secret` for each one.

### Required for BOTH Repositories

| Secret Name   | Description                                                                 | Example Value                                       |
| :------------ | :-------------------------------------------------------------------------- | :-------------------------------------------------- |
| `EC2_HOST`      | The public IP address or DNS name of your AWS EC2 instance.                 | `54.123.45.67`                                      |
| `EC2_USER`      | The SSH username for your EC2 instance.                                     | `ubuntu`                                            |
| `EC2_SSH_KEY`   | The **full content** of the private SSH key (`.pem` file) for your EC2 instance. | `-----BEGIN OPENSSH PRIVATE KEY-----\n...\n-----END ...` |

### Required for `GrantThrive-frontend` ONLY

| Secret Name      | Description                                                                 | Example Value                                       |
| :--------------- | :-------------------------------------------------------------------------- | :-------------------------------------------------- |
| `VITE_API_URL`   | The full URL to the backend API, ending in `/api`.                          | `https://grantthrive.com/api`                         |
| `VITE_LOGIN_URL` | The full URL to the frontend login page.                                    | `https://app.grantthrive.com/login`                   |

### Required for `grantthrive-platform` ONLY

| Secret Name             | Description                                                                 | Example Value                                       |
| :---------------------- | :-------------------------------------------------------------------------- | :-------------------------------------------------- |
| `SECRET_KEY`            | A long, random string for Flask session signing.                            | `openssl rand -hex 32`                              |
| `DATABASE_URL`          | The full connection string for your production database (e.g., PostgreSQL). | `postgresql://user:pass@host:port/dbname`           |
| `MAIL_SERVER`           | The hostname of your SMTP server.                                           | `smtp.sendgrid.net`                                 |
| `MAIL_PORT`             | The port for your SMTP server.                                              | `587`                                               |
| `MAIL_USERNAME`         | The username for your SMTP server (often `apikey` for SendGrid).            | `apikey`                                            |
| `MAIL_PASSWORD`         | The password or API key for your SMTP server.                               | `SG.xxxxxxxx...`                                    |
| `MAIL_DEFAULT_SENDER`   | The default "From" address for emails sent by the platform.                 | `"GrantThrive" <noreply@grantthrive.com>`           |

---

## 3. SSL Certificate Setup (Let's Encrypt)

After the server setup script has run and you have pointed your domain DNS to the EC2 instance, run the following command on the server to install a free, auto-renewing SSL certificate from Let's Encrypt.

```bash
sudo certbot --nginx -d grantthrive.com -d www.grantthrive.com -d app.grantthrive.com -d admin.grantthrive.com -d map.grantthrive.com -d roi.grantthrive.com
```

Follow the on-screen prompts. Certbot will automatically update your Nginx configuration to enable HTTPS.

---

## 4. How It Works

-   **Zero-Downtime Deployments:** The pipeline uses an atomic symlink strategy. A new release is uploaded to a timestamped directory (e.g., `/srv/grantthrive/releases/20260301120000/`). Only after the new release is fully in place and (for the backend) dependencies are installed, a symbolic link at `/srv/grantthrive/current` is instantly swapped to point to the new release. Nginx and Gunicorn are then reloaded.

-   **Rollbacks:** If a deployment fails, you can easily roll back by SSHing into the server and running the `rollback.sh` script:

    ```bash
    # Roll back both frontend and backend to the previous version
    /home/ubuntu/grantthrive-platform/scripts/rollback.sh

    # Roll back only the frontend
    /home/ubuntu/grantthrive-platform/scripts/rollback.sh frontend
    ```

-   **Pruning:** The deployment script automatically keeps the 5 most recent releases and deletes any older ones to save disk space.
