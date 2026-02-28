"""
GrantThrive - Automated Monthly Performance Report Generator
============================================================
Generates comprehensive PDF performance reports for each council (admin user)
covering grants, applications, processing times, budget allocation,
community engagement, and cost savings for the previous calendar month.
"""

import os
import io
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image as RLImage
from sqlalchemy import func, case, and_, extract

from app import db
from app.models import Grant, Application, User, Review, CommunityVote, VotingSession

logger = logging.getLogger(__name__)

# ─── Colour palette aligned with GrantThrive brand ───────────────────────────
GT_DARK_GREEN  = colors.HexColor("#1A5C38")
GT_MID_GREEN   = colors.HexColor("#2E8B57")
GT_LIGHT_GREEN = colors.HexColor("#D4EDDA")
GT_ACCENT      = colors.HexColor("#F4A261")
GT_GREY_LIGHT  = colors.HexColor("#F8F9FA")
GT_GREY_MID    = colors.HexColor("#DEE2E6")
GT_TEXT        = colors.HexColor("#212529")
GT_WHITE       = colors.white

# ─── Cost benchmark constants (AUD) ──────────────────────────────────────────
MANUAL_COST_PER_APPLICATION = Decimal("85.00")   # industry benchmark for paper-based processing
PLATFORM_COST_PER_APPLICATION = Decimal("12.50") # estimated GrantThrive per-application cost


def _build_styles():
    """Return a dict of custom paragraph styles."""
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontSize=26,
            textColor=GT_WHITE,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=base["Normal"],
            fontSize=14,
            textColor=GT_WHITE,
            spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            parent=base["Heading2"],
            fontSize=13,
            textColor=GT_DARK_GREEN,
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold",
            borderPad=0,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=GT_TEXT,
            spaceAfter=4,
            leading=14,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#6C757D"),
            spaceAfter=2,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            parent=base["Normal"],
            fontSize=22,
            textColor=GT_DARK_GREEN,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#6C757D"),
            alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=base["Normal"],
            fontSize=8.5,
            textColor=GT_WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=base["Normal"],
            fontSize=8.5,
            textColor=GT_TEXT,
            alignment=TA_LEFT,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontSize=7.5,
            textColor=colors.HexColor("#ADB5BD"),
            alignment=TA_CENTER,
        ),
    }
    return styles


def _fmt_currency(value):
    """Format a numeric value as AUD currency string."""
    if value is None:
        return "$0.00"
    return f"${float(value):,.2f}"


def _fmt_int(value):
    """Format an integer with thousands separator."""
    if value is None:
        return "0"
    return f"{int(value):,}"


def _fmt_days(value):
    """Format a float as a days string."""
    if value is None:
        return "N/A"
    return f"{float(value):.1f} days"


def _fmt_pct(numerator, denominator):
    """Return a percentage string, safe against division by zero."""
    if not denominator:
        return "0.0%"
    return f"{(float(numerator) / float(denominator) * 100):.1f}%"


def _table_style(header_rows=1):
    """Return a standard TableStyle for data tables."""
    return TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, header_rows - 1), GT_DARK_GREEN),
        ("TEXTCOLOR",     (0, 0), (-1, header_rows - 1), GT_WHITE),
        ("FONTNAME",      (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, header_rows - 1), 8.5),
        ("ALIGN",         (0, 0), (-1, header_rows - 1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, header_rows - 1), 7),
        ("TOPPADDING",    (0, 0), (-1, header_rows - 1), 7),
        # Body rows
        ("FONTSIZE",      (0, header_rows), (-1, -1), 8.5),
        ("ROWBACKGROUNDS",(0, header_rows), (-1, -1), [GT_WHITE, GT_GREY_LIGHT]),
        ("ALIGN",         (1, header_rows), (-1, -1), "CENTER"),
        ("ALIGN",         (0, header_rows), (0, -1), "LEFT"),
        ("TOPPADDING",    (0, header_rows), (-1, -1), 5),
        ("BOTTOMPADDING", (0, header_rows), (-1, -1), 5),
        # Grid
        ("GRID",          (0, 0), (-1, -1), 0.4, GT_GREY_MID),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, GT_MID_GREEN),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ])


def _kpi_table(kpis, styles):
    """
    Build a single-row KPI banner.
    kpis: list of (value_str, label_str) tuples
    """
    cells = []
    for value, label in kpis:
        cell = [
            Paragraph(value, styles["kpi_value"]),
            Paragraph(label, styles["kpi_label"]),
        ]
        cells.append(cell)

    col_width = (A4[0] - 1.5 * inch) / len(kpis)
    t = Table([cells], colWidths=[col_width] * len(kpis))
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GT_LIGHT_GREEN),
        ("BOX",           (0, 0), (-1, -1), 0.5, GT_MID_GREEN),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, GT_MID_GREEN),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _section_divider(styles):
    """Return a thin green horizontal rule with spacing."""
    return [
        Spacer(1, 4),
        HRFlowable(width="100%", thickness=1, color=GT_MID_GREEN, spaceAfter=4),
    ]


# ─── Main public function ─────────────────────────────────────────────────────

def generate_council_report(admin_user, year, month, output_dir="/tmp"):
    """
    Generate a comprehensive monthly performance PDF report for a single council.

    Parameters
    ----------
    admin_user : User
        The admin User record representing the council.
    year : int
        The reporting year (e.g. 2026).
    month : int
        The reporting month (1–12).
    output_dir : str
        Directory to write the PDF file.

    Returns
    -------
    str
        Absolute path to the generated PDF file.
    """
    # ── Reporting window ──────────────────────────────────────────────────────
    period_start = datetime(year, month, 1)
    next_month   = (period_start + timedelta(days=32)).replace(day=1)
    period_end   = next_month - timedelta(seconds=1)
    period_label = period_start.strftime("%B %Y")

    council_name = _derive_council_name(admin_user)

    logger.info(
        "Generating report for council '%s' (user_id=%d) — period: %s",
        council_name, admin_user.id, period_label,
    )

    # ── Fetch all data ────────────────────────────────────────────────────────
    data = _collect_metrics(admin_user, period_start, period_end)

    # ── Build PDF ─────────────────────────────────────────────────────────────
    safe_name = admin_user.username.replace(" ", "_")
    filename  = f"monthly_report_{safe_name}_{year}_{month:02d}.pdf"
    filepath  = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"Monthly Performance Report — {council_name} — {period_label}",
        author="GrantThrive Platform",
        subject="Automated Monthly Performance Report",
    )

    styles = _build_styles()
    story  = []

    # ── Cover section ─────────────────────────────────────────────────────────
    story += _build_cover(council_name, period_label, data, styles)

    # ── Section 1: Grant Overview ─────────────────────────────────────────────
    story += _section_grants(data, styles)

    # ── Section 2: Applications & Processing ─────────────────────────────────
    story += _section_applications(data, styles)

    # ── Section 3: Budget Allocation ─────────────────────────────────────────
    story += _section_budget(data, styles)

    # ── Section 4: Community Engagement ──────────────────────────────────────
    story += _section_community(data, styles)

    # ── Section 5: Cost Savings ───────────────────────────────────────────────
    story += _section_cost_savings(data, styles)

    # ── Section 6: Reviewer Performance ──────────────────────────────────────
    story += _section_reviewers(data, styles)

    # ── Footer note ───────────────────────────────────────────────────────────
    story += _build_footer(period_label, styles)

    doc.build(story)
    logger.info("Report written to %s", filepath)
    return filepath


# ─── Data collection ──────────────────────────────────────────────────────────

def _derive_council_name(admin_user):
    """Derive a display council name from the admin user record."""
    # Use organisation_name if the field exists on the model, otherwise fall back
    if hasattr(admin_user, "organisation_name") and admin_user.organisation_name:
        return admin_user.organisation_name
    return f"{admin_user.first_name} {admin_user.last_name} Council"


def _collect_metrics(admin_user, period_start, period_end):
    """
    Query the database and return a dict of all metrics needed for the report.
    All queries are scoped to grants owned by admin_user.
    """
    uid = admin_user.id

    # ── All grants for this council ───────────────────────────────────────────
    all_grants = Grant.query.filter_by(created_by=uid).all()
    grant_ids  = [g.id for g in all_grants]

    # ── Grant status breakdown ────────────────────────────────────────────────
    grants_by_status = {
        "draft":     sum(1 for g in all_grants if g.status == "draft"),
        "open":      sum(1 for g in all_grants if g.status == "open"),
        "closed":    sum(1 for g in all_grants if g.status == "closed"),
        "completed": sum(1 for g in all_grants if g.status == "completed"),
    }

    # ── Applications in reporting period ─────────────────────────────────────
    period_apps = (
        Application.query
        .filter(
            Application.grant_id.in_(grant_ids),
            Application.submitted_at >= period_start,
            Application.submitted_at <= period_end,
        )
        .all()
    ) if grant_ids else []

    # ── All-time applications for this council ────────────────────────────────
    all_apps = (
        Application.query
        .filter(Application.grant_id.in_(grant_ids))
        .all()
    ) if grant_ids else []

    # ── Application status counts (period) ───────────────────────────────────
    def _count_status(apps, status):
        return sum(1 for a in apps if a.status == status)

    apps_submitted    = len(period_apps)
    apps_approved     = _count_status(period_apps, "approved")
    apps_rejected     = _count_status(period_apps, "rejected")
    apps_under_review = _count_status(period_apps, "under_review")
    apps_draft        = _count_status(period_apps, "draft")

    # ── Financial metrics ─────────────────────────────────────────────────────
    def _safe_sum(apps, attr, filter_fn=None):
        total = Decimal("0")
        for a in apps:
            if filter_fn and not filter_fn(a):
                continue
            val = getattr(a, attr, None)
            if val is not None:
                total += Decimal(str(val))
        return total

    total_requested_period = _safe_sum(period_apps, "amount_requested")
    total_approved_period  = _safe_sum(
        period_apps, "amount_requested", filter_fn=lambda a: a.status == "approved"
    )

    # Budget totals across all grants
    total_budget_all = sum(
        Decimal(str(g.total_budget)) for g in all_grants if g.total_budget
    )

    # Per-grant budget utilisation
    grant_budget_rows = []
    for g in all_grants:
        g_apps = [a for a in all_apps if a.grant_id == g.id]
        approved_amt = _safe_sum(
            g_apps, "amount_requested", filter_fn=lambda a: a.status == "approved"
        )
        budget = Decimal(str(g.total_budget)) if g.total_budget else Decimal("0")
        utilisation = (approved_amt / budget * 100) if budget else Decimal("0")
        grant_budget_rows.append({
            "title":       g.title,
            "status":      g.status,
            "budget":      budget,
            "approved":    approved_amt,
            "utilisation": utilisation,
            "remaining":   budget - approved_amt,
            "app_count":   len(g_apps),
        })

    # ── Processing time (days from submitted_at to decision_date) ─────────────
    processing_times = []
    for a in period_apps:
        if a.submitted_at and a.decision_date:
            days = (a.decision_date - a.submitted_at).days
            if days >= 0:
                processing_times.append(days)

    avg_processing_days = (
        sum(processing_times) / len(processing_times)
        if processing_times else None
    )
    min_processing_days = min(processing_times) if processing_times else None
    max_processing_days = max(processing_times) if processing_times else None

    # ── Community engagement ──────────────────────────────────────────────────
    total_votes = 0
    avg_vote    = 0.0
    if grant_ids:
        vote_agg = (
            db.session.query(
                func.count(CommunityVote.id).label("cnt"),
                func.avg(CommunityVote.vote_value).label("avg"),
            )
            .join(Application, CommunityVote.application_id == Application.id)
            .filter(Application.grant_id.in_(grant_ids))
            .first()
        )
        if vote_agg and vote_agg.cnt:
            total_votes = int(vote_agg.cnt)
            avg_vote    = float(vote_agg.avg or 0)

    # Voting sessions for this council's grants
    voting_sessions = (
        VotingSession.query
        .filter(VotingSession.grant_id.in_(grant_ids))
        .all()
    ) if grant_ids else []

    # Applications with at least one community vote
    apps_with_votes = (
        db.session.query(func.count(func.distinct(CommunityVote.application_id)))
        .join(Application, CommunityVote.application_id == Application.id)
        .filter(Application.grant_id.in_(grant_ids))
        .scalar()
        or 0
    ) if grant_ids else 0

    # ── Reviews ───────────────────────────────────────────────────────────────
    reviews_period = (
        Review.query
        .join(Application, Review.application_id == Application.id)
        .filter(
            Application.grant_id.in_(grant_ids),
            Review.created_at >= period_start,
            Review.created_at <= period_end,
        )
        .all()
    ) if grant_ids else []

    completed_reviews = [r for r in reviews_period if r.is_complete]
    review_completion_rate = (
        len(completed_reviews) / len(reviews_period) * 100
        if reviews_period else 0
    )

    # ── Cost savings ──────────────────────────────────────────────────────────
    n_apps = len(period_apps)
    manual_cost   = MANUAL_COST_PER_APPLICATION * n_apps
    platform_cost = PLATFORM_COST_PER_APPLICATION * n_apps
    cost_saving   = manual_cost - platform_cost
    saving_pct    = (cost_saving / manual_cost * 100) if manual_cost else Decimal("0")

    # ── Compile and return ────────────────────────────────────────────────────
    return {
        # Meta
        "council_name":      _derive_council_name(admin_user),
        "admin_email":       admin_user.email,
        "generated_at":      datetime.utcnow(),
        # Grants
        "all_grants":        all_grants,
        "grants_by_status":  grants_by_status,
        "grant_budget_rows": grant_budget_rows,
        "total_budget_all":  total_budget_all,
        # Applications
        "apps_submitted":    apps_submitted,
        "apps_approved":     apps_approved,
        "apps_rejected":     apps_rejected,
        "apps_under_review": apps_under_review,
        "apps_draft":        apps_draft,
        "total_requested":   total_requested_period,
        "total_approved":    total_approved_period,
        "approval_rate":     (apps_approved / apps_submitted * 100) if apps_submitted else 0,
        # Processing
        "avg_processing_days": avg_processing_days,
        "min_processing_days": min_processing_days,
        "max_processing_days": max_processing_days,
        # Community
        "total_votes":       total_votes,
        "avg_vote":          avg_vote,
        "voting_sessions":   voting_sessions,
        "apps_with_votes":   apps_with_votes,
        # Reviews
        "reviews_total":     len(reviews_period),
        "reviews_completed": len(completed_reviews),
        "review_completion": review_completion_rate,
        # Cost savings
        "n_apps":            n_apps,
        "manual_cost":       manual_cost,
        "platform_cost":     platform_cost,
        "cost_saving":       cost_saving,
        "saving_pct":        saving_pct,
    }


# ─── PDF section builders ──────────────────────────────────────────────────────

def _build_cover(council_name, period_label, data, styles):
    """Build the cover / header block of the report."""
    story = []

    # Green banner background via a coloured table
    banner_data = [[
        Paragraph(f"GrantThrive", styles["cover_sub"]),
        Paragraph(f"Monthly Performance Report", styles["cover_title"]),
        Paragraph(f"{council_name}", styles["cover_sub"]),
        Paragraph(f"Reporting Period: {period_label}", styles["cover_sub"]),
        Paragraph(
            f"Generated: {data['generated_at'].strftime('%d %B %Y at %H:%M UTC')}",
            styles["cover_sub"],
        ),
    ]]
    banner = Table(
        [[Paragraph(item, styles["cover_sub"]) for item in [
            "GrantThrive",
            f"Monthly Performance Report",
            council_name,
            f"Reporting Period: {period_label}",
            f"Generated: {data['generated_at'].strftime('%d %B %Y at %H:%M UTC')}",
        ]]],
        colWidths=[A4[0] - 1.5 * inch],
    )

    # Simpler approach: stacked paragraphs inside a coloured box
    cover_inner = [
        Paragraph("GrantThrive Platform", styles["cover_sub"]),
        Spacer(1, 4),
        Paragraph("Monthly Performance Report", styles["cover_title"]),
        Spacer(1, 6),
        Paragraph(council_name, styles["cover_sub"]),
        Spacer(1, 4),
        Paragraph(f"Reporting Period: {period_label}", styles["cover_sub"]),
        Spacer(1, 4),
        Paragraph(
            f"Generated: {data['generated_at'].strftime('%d %B %Y at %H:%M UTC')}",
            styles["cover_sub"],
        ),
    ]

    cover_table = Table([[cover_inner]], colWidths=[A4[0] - 1.5 * inch])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GT_DARK_GREEN),
        ("TOPPADDING",    (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.3 * inch))

    # KPI banner
    kpis = [
        (_fmt_int(len(data["all_grants"])),    "Total Grants"),
        (_fmt_int(data["apps_submitted"]),      "Applications\n(This Period)"),
        (_fmt_currency(data["total_approved"]), "Approved\nFunding"),
        (f"{data['approval_rate']:.1f}%",       "Approval Rate"),
        (_fmt_currency(data["cost_saving"]),    "Estimated\nCost Savings"),
    ]
    story.append(_kpi_table(kpis, styles))
    story.append(Spacer(1, 0.2 * inch))

    return story


def _section_grants(data, styles):
    """Section 1 — Grant Program Overview."""
    story = []
    story.append(Paragraph("1. Grant Program Overview", styles["section_heading"]))
    story += _section_divider(styles)

    story.append(Paragraph(
        f"As at the end of the reporting period, {data['council_name']} administers "
        f"<b>{len(data['all_grants'])}</b> grant program(s) through the GrantThrive platform. "
        f"The table below summarises each program's status, total budget, number of applications "
        f"received, and budget utilisation.",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    if not data["grant_budget_rows"]:
        story.append(Paragraph("No grant programs found for this council.", styles["small"]))
        return story

    # Status summary bar
    gs = data["grants_by_status"]
    status_data = [
        ["Status", "Count"],
        ["Open",      gs.get("open", 0)],
        ["Closed",    gs.get("closed", 0)],
        ["Completed", gs.get("completed", 0)],
        ["Draft",     gs.get("draft", 0)],
    ]
    st = Table(status_data, colWidths=[1.2 * inch, 0.8 * inch])
    st.setStyle(_table_style())
    story.append(KeepTogether([
        Paragraph("Grant Status Summary", styles["body"]),
        Spacer(1, 4),
        st,
    ]))
    story.append(Spacer(1, 10))

    # Per-grant detail table
    header = ["Grant Program", "Status", "Total Budget", "Approved", "Utilisation", "Remaining", "Applications"]
    rows   = [header]
    for row in data["grant_budget_rows"]:
        rows.append([
            Paragraph(row["title"][:55], styles["table_cell"]),
            row["status"].capitalize(),
            _fmt_currency(row["budget"]),
            _fmt_currency(row["approved"]),
            f"{float(row['utilisation']):.1f}%",
            _fmt_currency(row["remaining"]),
            _fmt_int(row["app_count"]),
        ])

    col_widths = [2.4*inch, 0.7*inch, 1.0*inch, 1.0*inch, 0.8*inch, 1.0*inch, 0.8*inch]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 6))

    # Total row
    total_row_data = [[
        Paragraph("<b>TOTAL</b>", styles["body"]),
        "",
        Paragraph(f"<b>{_fmt_currency(data['total_budget_all'])}</b>", styles["body"]),
    ]]
    story.append(Spacer(1, 4))

    return story


def _section_applications(data, styles):
    """Section 2 — Applications and Processing Times."""
    story = []
    story.append(Paragraph("2. Applications & Processing Times", styles["section_heading"]))
    story += _section_divider(styles)

    story.append(Paragraph(
        f"During {data['generated_at'].strftime('%B %Y')}, the platform received "
        f"<b>{_fmt_int(data['apps_submitted'])}</b> application(s). "
        f"Of these, <b>{_fmt_int(data['apps_approved'])}</b> were approved "
        f"({data['approval_rate']:.1f}% approval rate), "
        f"<b>{_fmt_int(data['apps_rejected'])}</b> were rejected, and "
        f"<b>{_fmt_int(data['apps_under_review'])}</b> remain under review.",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    # Application status table
    app_status_data = [
        ["Status",        "Count", "% of Total"],
        ["Submitted",     data["apps_submitted"],    "100%"],
        ["Approved",      data["apps_approved"],     _fmt_pct(data["apps_approved"],     data["apps_submitted"])],
        ["Rejected",      data["apps_rejected"],     _fmt_pct(data["apps_rejected"],     data["apps_submitted"])],
        ["Under Review",  data["apps_under_review"], _fmt_pct(data["apps_under_review"], data["apps_submitted"])],
        ["Draft",         data["apps_draft"],        _fmt_pct(data["apps_draft"],        data["apps_submitted"])],
    ]
    t = Table(app_status_data, colWidths=[2.0*inch, 1.0*inch, 1.2*inch])
    t.setStyle(_table_style())
    story.append(KeepTogether([
        Paragraph("Application Status Breakdown", styles["body"]),
        Spacer(1, 4),
        t,
    ]))
    story.append(Spacer(1, 10))

    # Processing times
    story.append(Paragraph("Processing Time Analysis", styles["body"]))
    story.append(Spacer(1, 4))
    if data["avg_processing_days"] is not None:
        pt_data = [
            ["Metric",           "Value"],
            ["Average",          _fmt_days(data["avg_processing_days"])],
            ["Fastest",          _fmt_days(data["min_processing_days"])],
            ["Slowest",          _fmt_days(data["max_processing_days"])],
            ["Applications with decision", _fmt_int(
                sum(1 for _ in range(1))  # placeholder — computed inside _collect_metrics
            )],
        ]
        # Recalculate count of apps with a decision for display
        pt_data[4][1] = _fmt_int(
            data["apps_approved"] + data["apps_rejected"]
        )
        t2 = Table(pt_data, colWidths=[2.5*inch, 1.5*inch])
        t2.setStyle(_table_style())
        story.append(t2)
    else:
        story.append(Paragraph(
            "No applications with completed decisions were recorded in this period.",
            styles["small"],
        ))

    story.append(Spacer(1, 6))
    return story


def _section_budget(data, styles):
    """Section 3 — Budget Allocation."""
    story = []
    story.append(Paragraph("3. Budget Allocation", styles["section_heading"]))
    story += _section_divider(styles)

    story.append(Paragraph(
        f"The combined total budget across all grant programs managed by "
        f"{data['council_name']} is <b>{_fmt_currency(data['total_budget_all'])}</b>. "
        f"During the reporting period, <b>{_fmt_currency(data['total_approved'])}</b> "
        f"was approved for disbursement, representing "
        f"<b>{_fmt_pct(data['total_approved'], data['total_budget_all'])}</b> of the "
        f"combined budget.",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    budget_summary = [
        ["Budget Metric",              "Amount (AUD)"],
        ["Total Combined Budget",      _fmt_currency(data["total_budget_all"])],
        ["Total Requested (Period)",   _fmt_currency(data["total_requested"])],
        ["Total Approved (Period)",    _fmt_currency(data["total_approved"])],
        ["Remaining (Unallocated)",    _fmt_currency(data["total_budget_all"] - data["total_approved"])],
    ]
    t = Table(budget_summary, colWidths=[2.8*inch, 1.8*inch])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 6))
    return story


def _section_community(data, styles):
    """Section 4 — Community Engagement."""
    story = []
    story.append(Paragraph("4. Community Engagement", styles["section_heading"]))
    story += _section_divider(styles)

    story.append(Paragraph(
        f"Community participation is a core feature of the GrantThrive platform. "
        f"Across all grant programs, the community has cast a total of "
        f"<b>{_fmt_int(data['total_votes'])}</b> vote(s), covering "
        f"<b>{_fmt_int(data['apps_with_votes'])}</b> application(s). "
        f"The average community rating is <b>{data['avg_vote']:.2f}</b> out of 5.",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    engagement_data = [
        ["Engagement Metric",             "Value"],
        ["Total Community Votes",         _fmt_int(data["total_votes"])],
        ["Applications with Votes",       _fmt_int(data["apps_with_votes"])],
        ["Average Community Rating",      f"{data['avg_vote']:.2f} / 5.00"],
        ["Active Voting Sessions",        _fmt_int(len(data["voting_sessions"]))],
    ]
    t = Table(engagement_data, colWidths=[2.8*inch, 1.8*inch])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 6))
    return story


def _section_cost_savings(data, styles):
    """Section 5 — Cost Savings."""
    story = []
    story.append(Paragraph("5. Cost Savings & Efficiency", styles["section_heading"]))
    story += _section_divider(styles)

    story.append(Paragraph(
        f"By processing grant applications through the GrantThrive digital platform "
        f"rather than traditional paper-based workflows, {data['council_name']} "
        f"achieved an estimated cost saving of "
        f"<b>{_fmt_currency(data['cost_saving'])}</b> during this reporting period "
        f"({float(data['saving_pct']):.1f}% reduction). "
        f"This is calculated against an industry benchmark of "
        f"<b>{_fmt_currency(MANUAL_COST_PER_APPLICATION)}</b> per application for "
        f"manual processing, compared with the platform's estimated cost of "
        f"<b>{_fmt_currency(PLATFORM_COST_PER_APPLICATION)}</b> per application.",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    cost_data = [
        ["Cost Metric",                    "Amount (AUD)"],
        ["Applications Processed",         _fmt_int(data["n_apps"])],
        ["Estimated Manual Cost",          _fmt_currency(data["manual_cost"])],
        ["Estimated Platform Cost",        _fmt_currency(data["platform_cost"])],
        ["Estimated Saving",               _fmt_currency(data["cost_saving"])],
        ["Saving Percentage",              f"{float(data['saving_pct']):.1f}%"],
    ]
    t = Table(cost_data, colWidths=[2.8*inch, 1.8*inch])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Note: Cost benchmarks are based on published local government grant administration "
        "research. Actual savings may vary depending on council size and workflow complexity.",
        styles["small"],
    ))
    story.append(Spacer(1, 6))
    return story


def _section_reviewers(data, styles):
    """Section 6 — Reviewer Performance."""
    story = []
    story.append(Paragraph("6. Review & Assessment Activity", styles["section_heading"]))
    story += _section_divider(styles)

    story.append(Paragraph(
        f"During the reporting period, <b>{_fmt_int(data['reviews_total'])}</b> "
        f"review(s) were initiated, of which "
        f"<b>{_fmt_int(data['reviews_completed'])}</b> were completed "
        f"(completion rate: <b>{data['review_completion']:.1f}%</b>).",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    review_data = [
        ["Review Metric",              "Value"],
        ["Reviews Initiated",          _fmt_int(data["reviews_total"])],
        ["Reviews Completed",          _fmt_int(data["reviews_completed"])],
        ["Completion Rate",            f"{data['review_completion']:.1f}%"],
    ]
    t = Table(review_data, colWidths=[2.8*inch, 1.8*inch])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 6))
    return story


def _build_footer(period_label, styles):
    """Build the report footer."""
    story = [
        Spacer(1, 0.2 * inch),
        HRFlowable(width="100%", thickness=0.5, color=GT_GREY_MID),
        Spacer(1, 4),
        Paragraph(
            f"This report was automatically generated by the GrantThrive Platform on "
            f"{datetime.utcnow().strftime('%d %B %Y')} for the period {period_label}. "
            f"All figures are based on data recorded in the GrantThrive system at the "
            f"time of generation. For queries, contact your GrantThrive administrator.",
            styles["footer"],
        ),
    ]
    return story
