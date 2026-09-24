# GrantThrive Public Contact Forms

The public marketing contact form and launch waitlist are intentionally the only founder-contact channels exposed on GrantThrive. They are protected with Cloudflare Turnstile, rate-limited, and delivered through AWS SES. No destination inbox is placed in frontend code or rendered on a website page.

## Required deployment configuration

Create one Cloudflare Turnstile widget for the GrantThrive public site. Use **managed** challenge mode, register the deployed marketing hosts, and configure two actions: `contact` and `waitlist`. The site key is public and is supplied to the frontend build; the secret key must be stored only in the backend ECS task configuration or a referenced secret.

| Service | Configuration key | Purpose |
|---|---|---|
| Frontend build | `VITE_TURNSTILE_SITE_KEY` | Public Turnstile site key used to render the widget. |
| Backend ECS task | `TURNSTILE_SECRET_KEY` | Private secret used by the backend Siteverify request. |
| Backend ECS task | `TURNSTILE_EXPECTED_HOSTNAMES` | Comma-separated hostnames registered in the widget, for example the production and UAT marketing hosts. |
| Backend ECS task | `CONTACT_INBOX_EMAIL` | The approved business mailbox for public contact and waitlist delivery. Set this from the deployment secret store; do not commit it to source control. |
| Backend ECS task | `AWS_SES_FROM_EMAIL` | A verified SES sender address for GrantThrive notifications. |

## Endpoint behaviour

| Endpoint | Turnstile action | Subject format | Controls |
|---|---|---|---|
| `POST /api/contact` | `contact` | `GrantThrive - {enquiry type}` | Token validation, hostname/action validation, 5 requests/hour per IP, bounded inputs, metadata-only audit record. |
| `POST /api/waitlist` | `waitlist` | `GrantThrive - Waitlist signup` | Token validation, hostname/action validation, 5 requests/hour per IP, bounded inputs, metadata-only audit record. |

Cloudflare requires the backend to validate each token through Siteverify. Tokens are valid for five minutes and single-use, so the backend rejects a missing, expired, replayed or unverified token. The backend is deliberately fail-closed if the secret is unavailable or Cloudflare cannot be reached.

## Operational notes

Messages use the visitor's supplied address as the SES reply-to address, so replying to the delivered message replies to the visitor rather than revealing or embedding a founder inbox in public code. Audit records retain only the form type and delivery result, not message content or visitor email addresses.

Do not use `TURNSTILE_TEST_BYPASS` in UAT or production. It exists only for isolated automated tests.

## References

Cloudflare documents both [explicit widget rendering for SPAs](https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/) and mandatory [server-side Siteverify validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/).
