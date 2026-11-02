# Current delivery work

- [x] Deliver a protected role-aware Help & Guidance API for the current GrantThrive support library.
  - Return only the support cohorts relevant to the authenticated account’s actual role.
  - Return only public-visitor guidance to an unauthenticated request; reject invalid supplied bearer credentials rather than treating them as an anonymous request.
  - Supply a curated Top 10 for each actual account role, searchable plain-language guidance, and contextual topic links without returning cross-role data.

- [x] Preserve the established GrantThrive permission and safety boundaries in every response.
  - Do not grant or imply permissions beyond role and council scope.
  - Keep community voting advisory and non-binding, AI advisory-only and non-decisional, and public map guidance free of private applicant-location disclosure.
  - Add focused tests for anonymous, invalid-token, role-filtered, query, and contextual-topic responses.

Verified 2 November 2026: the focused support suite passes 10 tests; the full backend unittest suite passes 31 tests; Python compilation, FAQ integrity (six cohorts / 180 questions), and `git diff --check` pass.

- [x] Complete the six-cohort Help & Guidance permission and contextual-link audit.
  - Verify System Administrator, Council Administrator, Council Staff / Assessor, Applicant (professional consultant), Community Member, and Public Visitor responses expose only their mapped cohort content and permitted contextual topics.
  - Ensure every returned contextual topic refers only to a guidance answer rendered in that response, including when a plain-language search is active.
  - Ensure staff invitations are not presented to Council Staff / Assessors, and advisory-voting/public-map references use the correct Community Member and Public Visitor answers.
  - Support controlled plain-language variants for reviewer/recusal and vote/voting, enforce the 120-character query limit, and retain invalid-token and unknown-role fail-closed behavior.
  - Re-run the focused support suite and the complete backend unit suite after the audit.

Verified 2 November 2026: focused support coverage passes 12 tests and the complete backend unit suite passes 33 tests. The role matrix confirms every contextual question reference is rendered for the current role, and no cohort can use contextual help or search to access another cohort’s content.
