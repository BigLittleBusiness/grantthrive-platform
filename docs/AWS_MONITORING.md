> # GrantThrive: AWS Resource Monitoring Guide

This guide provides a practical plan for monitoring the health, performance, and cost of the GrantThrive platform's AWS resources. Effective monitoring is crucial for ensuring reliability, managing costs, and identifying potential issues before they impact users.

We will use **Amazon CloudWatch** as the central tool for collecting metrics, creating dashboards, and setting alarms.

---

## 1. Core Concepts: The Monitoring Framework

Our monitoring strategy is based on three activities:

1.  **Collecting Metrics:** AWS services automatically publish performance metrics to CloudWatch (e.g., CPU usage, request counts).
2.  **Visualizing Data (Dashboards):** We will create a centralized dashboard in CloudWatch to get a single-pane-of-glass view of the entire application stack.
3.  **Setting Alarms:** We will configure CloudWatch Alarms to automatically notify you (e.g., via email or Slack) when a metric crosses a defined threshold, allowing you to act proactively.

---

## 2. Monitoring the EC2 Backend Server

The EC2 instance runs the core Flask application. We need to monitor both the server's health and the application's performance.

### Key Metrics to Watch

| Metric | Threshold (Example) | Why it Matters |
| :--- | :--- | :--- |
| **`CPUUtilization`** | `> 80% for 15 minutes` | High CPU can indicate an overloaded server, leading to slow API responses. Sustained high usage may mean it's time to upgrade the instance type. |
| **`StatusCheckFailed`** | `> 0 for 5 minutes` | This indicates a problem with the underlying hardware or the instance itself. AWS may need to intervene. An alarm here is critical. |
| **`NetworkIn` / `NetworkOut`** | (Spike detection) | Sudden, unexpected spikes can indicate a traffic surge, a misbehaving client, or a potential security event. |

### Setting Up EC2 Alarms

1.  Navigate to the **CloudWatch Console** > **Alarms** > **All alarms**.
2.  Click **Create alarm**.
3.  Click **Select metric**.
4.  Choose **EC2 > Per-Instance Metrics** and find your `grantthrive-backend-server` instance.
5.  Select the `CPUUtilization` metric.
6.  **Conditions:**
    *   **Statistic:** `Average`
    *   **Period:** `5 minutes`
    *   **Threshold type:** `Static`
    *   **Whenever CPUUtilization is...** `Greater` > `80`.
7.  **Notification:**
    *   Choose an existing **SNS (Simple Notification Service) topic** or create a new one to send an email notification.
8.  Give the alarm a name (e.g., `grantthrive-backend-cpu-high`) and create it.
9.  **Repeat this process** for the `StatusCheckFailed` metric (set the threshold to `> 0`).

### Application-Level Logging

For deeper insights, the Flask application's logs should be sent to **CloudWatch Logs**. This allows you to search for specific errors and create metric filters (e.g., to count the number of 500 errors).

**Action:** Configure a logging library in Flask (like `watchtower`) to send application logs directly to a CloudWatch Log Group.

---

## 3. Monitoring the RDS Database

Database performance is critical for the entire platform. RDS provides detailed metrics to monitor its health.

### Key Metrics to Watch

| Metric | Threshold (Example) | Why it Matters |
| :--- | :--- | :--- |
| **`CPUUtilization`** | `> 80% for 15 minutes` | High CPU on the database can be caused by slow queries or high load. This is a primary indicator of database performance issues. |
| **`DatabaseConnections`** | `> 80% of max` | Nearing the maximum connection limit can cause the application to fail when trying to connect. This can indicate connection leaks in the app. |
| **`FreeableMemory`** | `< 256 MB for 10 minutes` | Low freeable memory indicates the database is under memory pressure, which can lead to swapping and poor performance. |
| **`FreeStorageSpace`** | `< 5 GB` | Running out of storage can cause the database to stop functioning. This is a critical alert to have. |

### Setting Up RDS Alarms

Follow the same process as for EC2 alarms, but select **RDS > Per-Database Metrics** and choose your `grantthrive-prod-db` instance. Create alarms for each of the key metrics listed above with the recommended thresholds.

---

## 4. Monitoring the CloudFront Frontend

CloudFront metrics give you insight into your user-facing traffic and frontend performance.

### Key Metrics to Watch

| Metric | Threshold (Example) | Why it Matters |
| :--- | :--- | :--- |
| **`Requests`** | (Spike detection) | Provides a view of total traffic. Sudden drops can indicate an outage, while spikes can indicate high user activity or a DDoS attack. |
| **`4xxErrorRate`** | `> 2% for 5 minutes` | A high rate of 4xx errors (like 404 Not Found) can indicate broken links or issues with how your frontend is trying to access assets. |
| **`5xxErrorRate`** | `> 1% for 5 minutes` | Any 5xx errors from CloudFront are serious and indicate a server-side problem at the edge or with the origin (S3). This requires immediate investigation. |
| **`CacheHitRate`** | `< 90%` | A low cache hit rate means CloudFront is frequently going back to your S3 bucket, increasing latency and cost. It may indicate a misconfiguration in caching behavior. |

### Setting Up CloudFront Alarms

Again, follow the same process in the CloudWatch Console, selecting **CloudFront > Per-Distribution Metrics** and choosing your GrantThrive distribution. Create alarms for the `4xxErrorRate` and `5xxErrorRate` metrics.

---

## 5. Critical Best Practice: Billing Alarms

One of the most important alarms you can set is a **Billing Alarm**. This will notify you if your estimated AWS bill exceeds a certain amount, protecting you from unexpected costs.

1.  Navigate to the **Billing & Cost Management Dashboard**.
2.  Go to **Budgets** and create a new budget.
3.  Set a monthly cost budget (e.g., $50).
4.  Configure an **Alert** to notify you when the actual or forecasted cost exceeds a percentage of your budget (e.g., 80%).

---

## 6. Creating a Central Dashboard

Finally, bring the most important metrics together into a single dashboard.

1.  In the **CloudWatch Console**, go to **Dashboards** and click **Create dashboard**.
2.  Name it `GrantThrive-Platform-Health`.
3.  Add widgets for each of the key metrics identified above for EC2, RDS, and CloudFront.
4.  Organize the dashboard logically (e.g., by service).

This dashboard will be your primary destination for quickly checking the status of the entire platform at a glance.
