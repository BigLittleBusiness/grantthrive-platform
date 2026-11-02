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
