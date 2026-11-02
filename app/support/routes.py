"""Role-scoped Help & Guidance endpoint."""

from __future__ import annotations

from flask import jsonify, request

from app.common.permissions import _resolve_user_from_token
from app.support import bp
from app.support.knowledge_base import COHORTS_BY_ID, QUESTIONS_BY_ID


# Roles are mapped here rather than accepted from a request parameter.  This is
# an explicit data-boundary allow-list: a caller can never select another
# cohort's guidance through the API.
ROLE_GUIDANCE = {
    "system_admin": {
        "label": "System Administrator",
        "cohorts": ("system_administrator",),
    },
    "council_admin": {
        "label": "Council Administrator",
        "cohorts": ("council_administrator",),
    },
    "council_staff": {
        "label": "Council Staff / Assessor",
        "cohorts": ("council_staff_assessor",),
    },
    "professional_consultant": {
        "label": "Applicant",
        "cohorts": ("applicant",),
    },
    "community_member": {
        "label": "Community Member",
        "cohorts": ("applicant", "community_member"),
    },
    # Defensive mappings for future stored role literals. They deliberately
    # expose only their own cohort rather than inheriting another role's data.
    "applicant": {
        "label": "Applicant",
        "cohorts": ("applicant",),
    },
    "public_visitor": {
        "label": "Public Visitor",
        "cohorts": ("public_visitor",),
    },
}

PUBLIC_VISITOR = {
    "role": "public_visitor",
    "label": "Public Visitor",
    "cohorts": ("public_visitor",),
}


# Each role has a fixed, curated list of ten quick-start questions. The
# community-member list is intentionally split across both applicable cohorts,
# rather than returning twenty items.
TOP_QUESTION_IDS_BY_ROLE = {
    "system_admin": tuple(f"system_administrator-{number:02d}" for number in range(1, 11)),
    "council_admin": tuple(f"council_administrator-{number:02d}" for number in range(1, 11)),
    "council_staff": tuple(f"council_staff_assessor-{number:02d}" for number in range(1, 11)),
    "professional_consultant": tuple(f"applicant-{number:02d}" for number in range(1, 11)),
    "community_member": (
        "applicant-01",
        "applicant-09",
        "applicant-12",
        "applicant-18",
        "applicant-20",
        "community_member-01",
        "community_member-08",
        "community_member-13",
        "community_member-19",
        "community_member-24",
    ),
    "applicant": tuple(f"applicant-{number:02d}" for number in range(1, 11)),
    "public_visitor": tuple(f"public_visitor-{number:02d}" for number in range(1, 11)),
}


CONTEXTUAL_TOPICS = (
    {
        "id": "staff-invitations",
        "label": "Staff invitations and access",
        "description": "Adding staff, approving staff requests, and managing council access.",
        "question_ids": (
            "council_administrator-20",
            "council_administrator-21",
            "council_administrator-22",
        ),
    },
    {
        "id": "reviewer-assignment",
        "label": "Reviewer assignment and recusal",
        "description": "Setting assessment teams, assigning reviewers, self-assignment, and conflicts of interest.",
        "question_ids": (
            "council_administrator-11",
            "council_administrator-17",
            "council_administrator-18",
            "council_staff_assessor-15",
            "council_staff_assessor-16",
            "council_staff_assessor-20",
        ),
    },
    {
        "id": "reports-exports",
        "label": "Reports and exports",
        "description": "Viewing council analytics and exporting the displayed data.",
        "question_ids": ("council_administrator-29",),
    },
    {
        "id": "subscription-changes",
        "label": "Subscriptions and billing",
        "description": "Starting, managing, troubleshooting, and changing council subscription services.",
        "question_ids": (
            "council_administrator-23",
            "council_administrator-24",
            "council_administrator-26",
        ),
    },
    {
        "id": "application-documents",
        "label": "Application documents",
        "description": "Uploading, validating, removing, and accessing application supporting documents.",
        "question_ids": (
            "applicant-18",
            "applicant-19",
            "council_staff_assessor-23",
        ),
    },
    {
        "id": "application-submission",
        "label": "Application submission",
        "description": "Reviewing declarations, submitting an application, and handling post-submission requests.",
        "question_ids": (
            "applicant-20",
            "applicant-21",
            "applicant-22",
        ),
    },
    {
        "id": "council-provisioning",
        "label": "Council provisioning",
        "description": "Reviewing registrations, creating councils, and provisioning council users.",
        "question_ids": (
            "system_administrator-12",
            "system_administrator-13",
            "system_administrator-14",
            "system_administrator-15",
            "system_administrator-16",
            "system_administrator-18",
        ),
    },
    {
        "id": "pricing-management",
        "label": "Pricing management",
        "description": "Updating published subscription pricing or restoring approved defaults.",
        "question_ids": (
            "system_administrator-24",
            "system_administrator-25",
        ),
    },
    {
        "id": "mfa-security",
        "label": "MFA and account security",
        "description": "Setting up and managing authenticator MFA and administrator password security.",
        "question_ids": (
            "system_administrator-07",
            "system_administrator-08",
            "system_administrator-09",
        ),
    },
    {
        "id": "ai-guardrails",
        "label": "AI guardrails",
        "description": "Using AI drafting support safely without delegating funding decisions.",
        "question_ids": (
            "system_administrator-28",
            "council_administrator-12",
            "council_staff_assessor-29",
            "applicant-30",
            "community_member-30",
            "public_visitor-30",
        ),
    },
    {
        "id": "advisory-voting",
        "label": "Advisory community voting",
        "description": "Understanding the non-binding role of community voting in council decisions.",
        "question_ids": (
            "system_administrator-29",
            "council_administrator-30",
            "council_staff_assessor-26",
            "community_member-23",
            "public_visitor-24",
        ),
    },
    {
        "id": "public-map-safety",
        "label": "Public map safety",
        "description": "Publishing only council-approved public locations and protecting applicant privacy.",
        "question_ids": (
            "system_administrator-30",
            "council_administrator-13",
            "council_staff_assessor-27",
            "community_member-26",
            "public_visitor-29",
        ),
    },
)

GUARDRAILS = (
    "Tenant and role boundaries remain in force for all guidance and platform actions.",
    "AI is advisory only and cannot decide funding.",
    "Community voting is advisory and non-binding; final funding decisions remain with the council.",
    "The public map must never reveal private applicant locations.",
    "Guidance cannot bypass council authority or formal workflows.",
)


# These variants keep plain-language searches aligned with the approved FAQ's
# terminology without broadening the search beyond all stated query concepts.
SEARCH_TERM_VARIANTS = {
    "reviewer": ("reviewer", "review", "recuse", "recusal", "assessor"),
    "recusal": ("recusal", "recuse", "conflict"),
    "vote": ("vote", "voting"),
    "voting": ("vote", "voting"),
}


def _question_matches(question: dict, query: str) -> bool:
    """Case-insensitively match a query against approved question text or answer."""
    if not query:
        return True
    searchable_text = f"{question['question']} {question['answer']}".casefold()
    return all(
        any(variant in searchable_text for variant in SEARCH_TERM_VARIANTS.get(term, (term,)))
        for term in query.split()
    )


def _serialise_cohort(cohort_id: str, query: str) -> dict:
    cohort = COHORTS_BY_ID[cohort_id]
    return {
        "id": cohort["id"],
        "label": cohort["label"],
        "description": cohort["description"],
        "questions": [
            {
                "id": question["id"],
                "question": question["question"],
                "answer": question["answer"],
            }
            for question in cohort["questions"]
            if _question_matches(question, query)
        ],
    }


def _serialise_top_questions(role: str, permitted_ids: set[str], query: str) -> list[dict]:
    top_questions = []
    for question_id in TOP_QUESTION_IDS_BY_ROLE.get(role, ()):
        if question_id not in permitted_ids:
            continue
        question = QUESTIONS_BY_ID[question_id]
        if not _question_matches(question, query):
            continue
        cohort = COHORTS_BY_ID[question["cohort_id"]]
        top_questions.append({
            "id": question["id"],
            "cohort_id": cohort["id"],
            "cohort_label": cohort["label"],
            "question": question["question"],
            "answer": question["answer"],
        })
    return top_questions


def _serialise_contextual_topics(
    permitted_ids: set[str], rendered_ids: set[str]
) -> list[dict]:
    """Return only visible topic question references safe for the current role."""
    topics = []
    for topic in CONTEXTUAL_TOPICS:
        permitted_topic_ids = [
            question_id
            for question_id in topic["question_ids"]
            if question_id in permitted_ids and question_id in rendered_ids
        ]
        if not permitted_topic_ids:
            continue
        topics.append({
            "id": topic["id"],
            "label": topic["label"],
            "description": topic["description"],
            "question_ids": permitted_topic_ids,
        })
    return topics


def _actor_from_request() -> tuple[dict, bool]:
    """Resolve a valid account, preserving anonymous access only when no header exists."""
    if "Authorization" not in request.headers:
        return PUBLIC_VISITOR, False

    try:
        user, error = _resolve_user_from_token()
    except (KeyError, TypeError, ValueError):
        # A signed token with malformed claims is still not a usable bearer
        # token. Keep its response consistent with other invalid tokens.
        return {"error": "Invalid token."}, True
    if error:
        return {"error": error}, True

    guidance = ROLE_GUIDANCE.get(user.role)
    if guidance is None:
        # An unknown future role receives no guidance rather than another role's
        # material. This protects the role boundary until a deliberate mapping
        # is introduced above.
        guidance = {
            "role": user.role,
            "label": "Authenticated user",
            "cohorts": (),
        }
    return {"role": user.role, **guidance}, True


@bp.route("/guidance", methods=["GET"])
def guidance():
    """Return approved guidance restricted to the caller's mapped cohort(s)."""
    actor_source, authenticated = _actor_from_request()
    if "error" in actor_source:
        return jsonify({"error": actor_source["error"]}), 401

    query_value = request.args.get("q", "")
    if not isinstance(query_value, str) or len(query_value) > 120:
        return jsonify({"error": "q must be a string of at most 120 characters."}), 400
    query = query_value.strip().casefold()

    cohort_ids = tuple(actor_source["cohorts"])
    permitted_ids = {
        question["id"]
        for cohort_id in cohort_ids
        for question in COHORTS_BY_ID[cohort_id]["questions"]
    }

    actor = {
        "role": actor_source["role"],
        "label": actor_source["label"],
        "authenticated": authenticated,
        "cohorts": list(cohort_ids),
    }
    cohorts = [_serialise_cohort(cohort_id, query) for cohort_id in cohort_ids]
    rendered_ids = {
        question["id"]
        for cohort in cohorts
        for question in cohort["questions"]
    }
    return jsonify({
        "actor": actor,
        "cohorts": cohorts,
        "top_questions": _serialise_top_questions(actor_source["role"], permitted_ids, query),
        "contextual_topics": _serialise_contextual_topics(permitted_ids, rendered_ids),
        "guardrails": list(GUARDRAILS),
        "total_questions": len(permitted_ids),
    })
