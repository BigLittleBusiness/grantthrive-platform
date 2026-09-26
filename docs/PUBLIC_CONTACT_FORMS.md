# GrantThrive Public Contact Forms

The public marketing contact form and launch waitlist are intentionally the only founder-contact channels exposed on GrantThrive. They are protected with Cloudflare Turnstile, rate-limited, and written to the GrantThrive database before any notification is sent. No destination inbox is placed in frontend code or rendered on a website page.

## Required deployment configuration

Create one Cloudflare Turnstile widget for the GrantThrive public site. Use **managed** challenge mode, register the deployed marketing hosts, and configure two actions: `contact` and `waitlist`. The site key is public and is supplied to the frontend build; the secret key must be stored only in the BinaryLane backend environment.

| Service | Configuration key | Purpose |
|---|---|---|
| Frontend build | `VITE_TURNSTILE_SITE_KEY` | Public Turnstile site key used to render the widget. |
| BinaryLane backend | `TURNSTILE_SECRET_KEY` | Private secret used by the backend Siteverify request. |
| BinaryLane backend | `TURNSTILE_EXPECTED_HOSTNAMES` | Comma-separated hostnames registered in the widget. |
| BinaryLane backend | `ADMIN_NOTIFICATION_EMAIL` | GrantThrive administrator mailbox receiving content-free alerts. Set through GitHub Actions secrets; do not commit it to source control. |
| BinaryLane backend | `ADMIN_DASHBOARD_URL` | Secure administrator dashboard link, defaulting to the Form Submissions view. |
| BinaryLane backend | `FIELD_ENCRYPTION_KEY` | AES-256-GCM key required before public submissions are stored. |
| BinaryLane backend | `AWS_SES_FROM_EMAIL` | A verified SES sender address for GrantThrive notifications. |

## Endpoint behaviour

| Endpoint | Turnstile action | Result | Controls |
|---|---|---|---|
| `POST /api/contact` | `contact` | Creates an encrypted contact record, then alerts the administrator. | Token validation, hostname/action validation, 5 requests/hour per IP, bounded inputs, database-first commit, metadata-only audit record. |
| `POST /api/waitlist` | `waitlist` | Creates an encrypted waitlist record, then alerts the administrator. | Token validation, hostname/action validation, 5 requests/hour per IP, bounded inputs, database-first commit, metadata-only audit record. |
| `GET/PATCH /api/admin/form-submissions` | N/A | Lists, reviews and updates protected records. | System-admin JWT/RBAC, paginated filters, encrypted fields, and audit records for privileged views/updates. |

Cloudflare requires the backend to validate each token through Siteverify. Tokens are valid for five minutes and single-use, so the backend rejects a missing, expired, replayed or unverified token. The backend is deliberately fail-closed if the secret is unavailable or Cloudflare cannot be reached.

## Operational notes

The database is the source of truth. Each successful verification creates the encrypted submission first; a failed notification cannot make a visitor's submission disappear. The administrator email subject is `GrantThrive - New form submission` and contains only a secure dashboard link—never a name, email address, organisation, phone number or message. Audit records retain only form type, status and notification result, not submission contents or visitor email addresses.

Do not use `TURNSTILE_TEST_BYPASS` in UAT or production. It exists only for isolated automated tests.

## References

Cloudflare documents both [explicit widget rendering for SPAs](https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/) and mandatory [server-side Siteverify validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/).
