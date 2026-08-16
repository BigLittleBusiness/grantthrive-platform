# GrantThrive — AWS Bedrock Guardrail Template

**Status:** Implementation template for the Grant Creation Assistant

> **Operating principle:** GrantThrive AI features provide advisory drafting and summarisation support only. They must not approve, reject, rank, allocate, or otherwise decide grant outcomes.

## 1. Intended First-Release Use

The first Bedrock integration supports `POST /api/ai/grant-suggestions`. The endpoint accepts a deliberately limited, non-applicant draft of a grant program and returns bounded suggestions for authorised council administrators.

| In scope | Out of scope |
|---|---|
| Eligibility wording, assessment criteria, timelines, required documents, plain language, accessibility and community-engagement suggestions | Funding allocation, applicant scoring, approval or rejection, ranking, legal advice, policy interpretation, applicant information, attachments, or autonomous changes |

## 2. Bedrock Guardrail Configuration

Create a Bedrock guardrail in the GrantThrive AWS account, publish a numbered version, and set its ID and version in the ECS task environment. Do not use the mutable `DRAFT` version in production.

### Guardrail name

`grantthrive-grant-assistant`

### Denied topic template

| Field | Template |
|---|---|
| Topic name | Automated grant funding decisions |
| Definition | Block content that recommends, determines, predicts, ranks, scores, approves, rejects, prioritises, or allocates funding to an individual, organisation, application, or project. GrantThrive AI is advisory only and may help improve grant-program wording, but cannot make grant decisions. |
| Example phrases | `Which applicant should receive funding?`; `Rank these applications`; `Approve this grant`; `Who is most deserving?`; `Allocate the budget between applicants` |
| Input blocked message | `GrantThrive AI can help improve a grant-program draft, but it cannot make or recommend funding decisions.` |
| Output blocked message | `GrantThrive AI cannot provide a funding decision, ranking, approval, rejection, or allocation recommendation.` |

### Sensitive-information policy template

Configure detection and masking/blocking for data that should never be sent or reproduced by this feature:

| Category | Recommended action |
|---|---|
| Credentials, API keys, passwords, tokens | Block |
| Financial account information | Block |
| Government identifiers | Block |
| Health and criminal-history information | Block |
| Contact details submitted accidentally in a draft | Mask or block, according to the council's approved privacy setting |

### Content policy template

Use the organisation's standard policy for harmful, abusive, violent, sexual, or discriminatory content. Configure a user-facing response that is neutral and does not expose implementation details.

### Word / phrase policy template

Create a managed or custom list for terms that should trigger review rather than be copied into public grant wording. Initial examples include discriminatory exclusion terms, unsupported guarantees, and language directing an AI to decide who receives funding. Maintain the final list through legal and policy review; do not rely on this template as a substitute for council policy.

## 3. Application Configuration

Set the following ECS task environment variables. The endpoint remains disabled unless the feature flag is explicitly enabled.

| Variable | Example / guidance |
|---|---|
| `AI_FEATURES_ENABLED` | `true` only after the pilot is approved; defaults to `false` |
| `AWS_REGION` | `ap-southeast-2` |
| `AWS_BEDROCK_MODEL_ID` | Approved Bedrock model ID or inference profile ID |
| `AWS_BEDROCK_GUARDRAIL_ID` | Published GrantThrive guardrail ID |
| `AWS_BEDROCK_GUARDRAIL_VERSION` | Immutable published version number |
| `AWS_BEDROCK_MAX_TOKENS` | `900` for this endpoint |
| `AWS_BEDROCK_TEMPERATURE` | `0.2` for stable, low-variance suggestions |

The ECS task role requires `bedrock:InvokeModel` only for the approved model or inference profile. If a Bedrock guardrail is used, grant the minimal additional permissions required for that deployed configuration. Do not add static AWS keys to production ECS environment variables; the boto3 client uses the ECS task role.

## 4. Prompt Injection and Data-Minimisation Controls

The API accepts only whitelisted grant-draft fields, each with bounded lengths. The endpoint rejects unexpected data, strips fields not required for grant-program drafting, and never accepts application records or file attachments.

The system prompt treats draft text as untrusted reference data. It directs the model to ignore instructions embedded in the draft and requires a strict JSON response. The API validates that response again before returning it to the frontend.

## 5. Audit and Retention

The endpoint creates an `AuditLog` record containing request metadata only: user ID, council ID, endpoint action, model ID, prompt version, input/output token counts, latency, suggestion count, and outcome. It does not store the submitted draft text or generated suggestions in the audit record.

## 6. Acceptance Criteria Before Enabling the Feature

- The endpoint is inaccessible while `AI_FEATURES_ENABLED=false`.
- Only `council_admin` and `system_admin` users can call it.
- A council user cannot generate suggestions on another council's saved grant.
- The request does not accept applicant information, attachments, or unknown fields.
- Responses always include the advisory disclaimer.
- A guardrail intervention produces a safe, generic user-facing message.
- Bedrock errors and malformed model output fail safely without exposing AWS error detail.
- A council officer tests representative draft grants and confirms suggestions are useful, accurate, and appropriately cautious.

## 7. References

The implementation uses Amazon Bedrock's `Converse` interface with a system prompt, structured `messages`, optional `guardrailConfig`, and a `bedrock:InvokeModel` permission requirement. [1] The optional guardrail configuration requires an identifier and version; when an intervention occurs, the response signals `guardrail_intervened`. [2]

[1]: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html "Amazon Bedrock Converse API"
[2]: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-converse-api.html "Use a guardrail with the Converse API"
