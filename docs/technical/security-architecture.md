# GrantThrive Security Architecture

This document describes the security architecture of the GrantThrive platform. Security is a top priority for GrantThrive, and the platform is designed to meet the stringent security requirements of Australian government organisations.

## 1. Authentication and Authorisation

- **JWT-based Authentication**: All user authentication is handled via JSON Web Tokens (JWTs). This provides a stateless and secure way to manage user sessions.
- **Role-Based Access Control (RBAC)**: The platform implements a robust RBAC system to control access to different features and data. The roles include `council_admin`, `council_staff`, and `community_user`.
- **Password Security**: User passwords are not stored in plaintext. Instead, they are hashed using the Werkzeug security library, which provides strong password hashing.

## 2. Data Protection

- **Data Encryption**: Sensitive data is encrypted both in transit (using TLS/SSL) and at rest.
- **Input Validation**: All user input is rigorously validated and sanitised to prevent common web vulnerabilities such as Cross-Site Scripting (XSS) and SQL injection.
- **Secure File Uploads**: File uploads are restricted by type and size to prevent malicious file uploads.

## 3. Compliance and Auditing

- **Audit Logging**: All significant actions taken on the platform are logged in the `audit_logs` table. This provides a complete audit trail for compliance and security analysis.
- **Australian Data Residency**: For Australian councils, all data is stored within Australia to comply with data residency requirements.

## 4. Production Security

- **Security Headers**: The platform uses a range of security headers (e.g., HSTS, CSP, X-Frame-Options) to protect against common web attacks.
- **Secure CORS Policy**: The Cross-Origin Resource Sharing (CORS) policy is configured to only allow requests from trusted domains.
- **Rate Limiting**: The API implements rate limiting to protect against denial-of-service (DoS) attacks.


