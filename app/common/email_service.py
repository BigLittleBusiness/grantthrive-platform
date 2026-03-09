"""
GrantThrive — Email Service (AWS SES)
======================================
Centralised transactional email layer.

All emails are sent via AWS SES using boto3.  In development / test
environments (when AWS_SES_ENABLED is False or credentials are absent),
every email is logged to the console instead of being sent so that
development can proceed without live AWS credentials.

Configuration (environment variables / .env):
    AWS_SES_ENABLED       = true | false   (default: false)
    AWS_SES_REGION        = ap-southeast-2
    AWS_ACCESS_KEY_ID     = <key>
    AWS_SECRET_ACCESS_KEY = <secret>
    AWS_SES_FROM_EMAIL    = hello@grantthrive.com
    FRONTEND_BASE_URL     = https://app.grantthrive.com   (used in email links)
"""

import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

FROM_EMAIL   = os.environ.get('AWS_SES_FROM_EMAIL', 'hello@grantthrive.com')
FROM_NAME    = 'GrantThrive'
FRONTEND_URL = os.environ.get('FRONTEND_BASE_URL', 'https://app.grantthrive.com')
MARKETING_URL = os.environ.get('MARKETING_BASE_URL', 'https://www.grantthrive.com')

# ── Shared HTML helpers ───────────────────────────────────────────────────────

def _email_wrapper(body_html: str, preheader: str = '') -> str:
    """Wrap body HTML in the standard GrantThrive email shell."""
    year = datetime.now().year
    preheader_span = (
        f'<span style="display:none;max-height:0;overflow:hidden;'
        f'mso-hide:all;">{preheader}&nbsp;</span>'
        if preheader else ''
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <style>
    body{{margin:0;padding:0;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f4f5;color:#1a2332}}
    .wrapper{{max-width:600px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08)}}
    .hdr{{background:#15803d;padding:28px 40px;text-align:center}}
    .hdr h1{{color:#fff;font-size:22px;font-weight:700;margin:0;letter-spacing:-.3px}}
    .hdr p{{color:#bbf7d0;font-size:13px;margin:4px 0 0}}
    .bdy{{padding:36px 40px}}
    .bdy h2{{font-size:19px;font-weight:700;color:#1a2332;margin:0 0 10px}}
    .bdy p{{font-size:15px;line-height:1.65;color:#37474f;margin:0 0 14px}}
    .info-box{{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:18px 22px;margin:20px 0}}
    .info-box p{{margin:3px 0;font-size:14px;color:#166534}}
    .info-box strong{{color:#14532d}}
    .cta-btn{{display:inline-block;background:#15803d;color:#fff!important;text-decoration:none;font-size:15px;font-weight:600;padding:13px 30px;border-radius:8px;margin:6px 0 20px}}
    .ftr{{background:#f8fafc;border-top:1px solid #e2e8f0;padding:20px 40px;text-align:center}}
    .ftr p{{font-size:12px;color:#94a3b8;margin:3px 0}}
    .ftr a{{color:#15803d;text-decoration:none}}
  </style>
</head>
<body>
  {preheader_span}
  <div class="wrapper">
    <div class="hdr">
      <h1>GrantThrive</h1>
      <p>Empowering councils. Engaging communities.</p>
    </div>
    <div class="bdy">
      {body_html}
    </div>
    <div class="ftr">
      <p>&copy; {year} GrantThrive. All rights reserved.</p>
      <p>
        <a href="{MARKETING_URL}/pages/contact.html">Contact Us</a> &middot;
        <a href="{MARKETING_URL}">grantthrive.com</a>
      </p>
      <p style="margin-top:10px;font-size:11px;">
        You received this email because you have an account with GrantThrive.
        <a href="{FRONTEND_URL}/portal/profile">Manage notification preferences</a>.
      </p>
    </div>
  </div>
</body>
</html>"""


# ── SES sender ────────────────────────────────────────────────────────────────

def _ses_enabled() -> bool:
    return os.environ.get('AWS_SES_ENABLED', 'false').lower() == 'true'


def send_email(to_email: str, subject: str, html_body: str, text_body: str = '') -> bool:
    """
    Send a transactional email via AWS SES (or log in dev mode).

    Returns True on success, False on failure.
    """
    full_html = _email_wrapper(html_body, preheader=subject)

    if not _ses_enabled():
        logger.info(
            "DEV MODE — Email not sent:\n  To: %s\n  Subject: %s",
            to_email, subject,
        )
        return True

    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client(
            'ses',
            region_name=os.environ.get('AWS_SES_REGION', 'ap-southeast-2'),
        )
        client.send_email(
            Source=f'{FROM_NAME} <{FROM_EMAIL}>',
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': full_html,  'Charset': 'UTF-8'},
                    'Text': {'Data': text_body or subject, 'Charset': 'UTF-8'},
                },
            },
        )
        logger.info("SES email sent to %s — %s", to_email, subject)
        return True

    except Exception as exc:
        logger.error("SES send failed to %s: %s", to_email, exc)
        return False


# ── Individual email builders ─────────────────────────────────────────────────

def send_registration_confirmation(to_email: str, first_name: str) -> bool:
    subject = "Welcome to GrantThrive — Confirm Your Registration"
    html = f"""
<h2>Hi {first_name}, welcome to GrantThrive!</h2>
<p>Your account has been created successfully. You can now browse grants, submit applications, and engage with your community.</p>
<a href="{FRONTEND_URL}" class="cta-btn">Go to Your Dashboard &rarr;</a>
<p>If you did not create this account, please <a href="{MARKETING_URL}/pages/contact.html" style="color:#15803d;">contact us</a> immediately.</p>
<p>We are glad to have you.<br><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nWelcome to GrantThrive! Your account is ready.\n\nVisit: {FRONTEND_URL}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_welcome_getting_started(to_email: str, first_name: str) -> bool:
    subject = "Getting started with GrantThrive"
    html = f"""
<h2>Hi {first_name}, here is how to get the most out of GrantThrive</h2>
<p>Your account has been active for 24 hours — here are three things to do right now:</p>
<div class="info-box">
  <p><strong>1. Browse available grants</strong> — Find grants that match your goals.</p>
  <p><strong>2. Submit an application</strong> — It only takes a few minutes.</p>
  <p><strong>3. Vote on community projects</strong> — Have your say on what gets funded.</p>
</div>
<a href="{FRONTEND_URL}" class="cta-btn">Explore Grants &rarr;</a>
<p>If you have any questions, reply to this email and our team will help.<br><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nHere are three things to do in GrantThrive:\n1. Browse grants\n2. Submit an application\n3. Vote on community projects\n\nVisit: {FRONTEND_URL}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_staff_added(to_email: str, first_name: str, council_name: str, role: str, temp_password: str) -> bool:
    subject = f"You have been added to {council_name} on GrantThrive"
    role_label = role.replace('_', ' ').title()
    html = f"""
<h2>Hi {first_name}, you have been added to {council_name}</h2>
<p>A Council Administrator has added you to <strong>{council_name}</strong> on GrantThrive as a <strong>{role_label}</strong>.</p>
<div class="info-box">
  <p><strong>Your login email:</strong> {to_email}</p>
  <p><strong>Temporary password:</strong> {temp_password}</p>
  <p><strong>Council:</strong> {council_name}</p>
  <p><strong>Your role:</strong> {role_label}</p>
</div>
<a href="{FRONTEND_URL}" class="cta-btn">Log In &rarr;</a>
<p style="font-size:13px;color:#64748b;">Please change your password after your first login. Your temporary password will expire in 72 hours.</p>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nYou have been added to {council_name} on GrantThrive as {role_label}.\n\nLogin: {FRONTEND_URL}\nEmail: {to_email}\nTemp password: {temp_password}\n\nPlease change your password after first login.\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_application_submitted(
    to_email: str, first_name: str, grant_title: str,
    application_id: int, council_name: str
) -> bool:
    subject = f"New application received — {grant_title}"
    link = f"{FRONTEND_URL}/portal/council/pending-approvals"
    html = f"""
<h2>A new application has been submitted</h2>
<p>Hi {first_name}, a community member has submitted an application for <strong>{grant_title}</strong> at <strong>{council_name}</strong>.</p>
<div class="info-box">
  <p><strong>Grant:</strong> {grant_title}</p>
  <p><strong>Application ID:</strong> #{application_id}</p>
  <p><strong>Council:</strong> {council_name}</p>
</div>
<a href="{link}" class="cta-btn">Review Application &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nA new application has been submitted for {grant_title} (#{application_id}).\n\nReview it at: {link}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_reviewer_assigned(
    to_email: str, first_name: str, grant_title: str,
    application_id: int, applicant_name: str
) -> bool:
    subject = f"You have been assigned to review an application — {grant_title}"
    link = f"{FRONTEND_URL}/portal/council/pending-approvals"
    html = f"""
<h2>Hi {first_name}, you have a new application to review</h2>
<p>You have been assigned to review an application for <strong>{grant_title}</strong>.</p>
<div class="info-box">
  <p><strong>Grant:</strong> {grant_title}</p>
  <p><strong>Application ID:</strong> #{application_id}</p>
  <p><strong>Applicant:</strong> {applicant_name}</p>
</div>
<a href="{link}" class="cta-btn">Review Now &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nYou have been assigned to review application #{application_id} for {grant_title} from {applicant_name}.\n\nReview at: {link}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_reviewer_reminder(
    to_email: str, first_name: str, grant_title: str,
    application_id: int, hours_pending: int
) -> bool:
    subject = f"Reminder: Application awaiting your review — {grant_title}"
    link = f"{FRONTEND_URL}/portal/council/pending-approvals"
    html = f"""
<h2>Hi {first_name}, a friendly reminder</h2>
<p>An application for <strong>{grant_title}</strong> has been waiting for your review for <strong>{hours_pending} hours</strong>.</p>
<div class="info-box">
  <p><strong>Application ID:</strong> #{application_id}</p>
  <p><strong>Pending for:</strong> {hours_pending} hours</p>
</div>
<a href="{link}" class="cta-btn">Review Now &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nApplication #{application_id} for {grant_title} has been waiting {hours_pending} hours for your review.\n\nReview at: {link}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_application_status_update(
    to_email: str, first_name: str, grant_title: str,
    new_status: str, application_id: int
) -> bool:
    status_labels = {
        'under_review': 'Under Review',
        'approved':     'Approved',
        'rejected':     'Unsuccessful',
    }
    status_messages = {
        'under_review': f'Your application for <strong>{grant_title}</strong> is now under review by the assessment team. We will be in touch once a decision has been made.',
        'approved':     f'Congratulations! Your application for <strong>{grant_title}</strong> has been <strong>approved</strong>. The council will be in contact with next steps.',
        'rejected':     f'Thank you for your application for <strong>{grant_title}</strong>. After careful consideration, your application was not successful this time. We encourage you to apply again in future rounds.',
    }
    label   = status_labels.get(new_status, new_status.replace('_', ' ').title())
    message = status_messages.get(new_status, f'Your application status has been updated to {label}.')
    subject = f"Application update: {label} — {grant_title}"
    link    = f"{FRONTEND_URL}/portal/community/dashboard"
    html = f"""
<h2>Hi {first_name}, your application has been updated</h2>
<p>{message}</p>
<div class="info-box">
  <p><strong>Grant:</strong> {grant_title}</p>
  <p><strong>Application ID:</strong> #{application_id}</p>
  <p><strong>Status:</strong> {label}</p>
</div>
<a href="{link}" class="cta-btn">View Your Dashboard &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nYour application #{application_id} for {grant_title} is now: {label}.\n\nView at: {link}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_voting_opened(
    to_email: str, first_name: str, session_title: str,
    council_name: str, closes_at: datetime, session_id: int
) -> bool:
    subject = f"Community voting is now open — {session_title}"
    closes_str = closes_at.strftime('%d %B %Y')
    link = f"{FRONTEND_URL}/portal/community/community-voting"
    html = f"""
<h2>Hi {first_name}, your vote matters</h2>
<p>A new community voting session is now open at <strong>{council_name}</strong>. Cast your vote before <strong>{closes_str}</strong>.</p>
<div class="info-box">
  <p><strong>Session:</strong> {session_title}</p>
  <p><strong>Council:</strong> {council_name}</p>
  <p><strong>Voting closes:</strong> {closes_str}</p>
</div>
<a href="{link}" class="cta-btn">Vote Now &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nCommunity voting is open for '{session_title}' at {council_name}. Closes {closes_str}.\n\nVote at: {link}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_voting_closes_soon(
    to_email: str, first_name: str, session_title: str,
    council_name: str, hours_remaining: int, session_id: int
) -> bool:
    subject = f"Voting closes in {hours_remaining} hours — {session_title}"
    link = f"{FRONTEND_URL}/portal/community/community-voting"
    html = f"""
<h2>Hi {first_name}, voting closes soon</h2>
<p>The community voting session <strong>{session_title}</strong> at <strong>{council_name}</strong> closes in <strong>{hours_remaining} hours</strong>. Don't miss your chance to have a say.</p>
<a href="{link}" class="cta-btn">Vote Now &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nVoting for '{session_title}' closes in {hours_remaining} hours.\n\nVote at: {link}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_results_published(
    to_email: str, first_name: str, grant_title: str,
    council_name: str, outcome: str
) -> bool:
    subject = f"Grant results published — {grant_title}"
    link = f"{FRONTEND_URL}/portal/community/public-results"
    outcome_msg = (
        f'Congratulations — your application was <strong>successful</strong>!'
        if outcome == 'approved'
        else f'Thank you for participating. The results for <strong>{grant_title}</strong> have been published.'
    )
    html = f"""
<h2>Hi {first_name}, grant results are in</h2>
<p>{outcome_msg}</p>
<div class="info-box">
  <p><strong>Grant:</strong> {grant_title}</p>
  <p><strong>Council:</strong> {council_name}</p>
</div>
<a href="{link}" class="cta-btn">View Results &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nResults for '{grant_title}' at {council_name} have been published.\n\nView at: {link}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_password_reset(to_email: str, first_name: str, reset_token: str) -> bool:
    subject = "Reset your GrantThrive password"
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    html = f"""
<h2>Hi {first_name}, here is your password reset link</h2>
<p>We received a request to reset your GrantThrive password. Click the button below to set a new password. This link expires in <strong>1 hour</strong>.</p>
<a href="{reset_link}" class="cta-btn">Reset Password &rarr;</a>
<p style="font-size:13px;color:#64748b;">If you did not request a password reset, you can safely ignore this email. Your password will not change.</p>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nReset your password: {reset_link}\n\nThis link expires in 1 hour.\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)


def send_monthly_digest(
    to_email: str, first_name: str, council_name: str,
    month_label: str, stats: dict
) -> bool:
    subject = f"Your {month_label} activity summary — {council_name}"
    link = f"{FRONTEND_URL}/portal/council/dashboard"
    html = f"""
<h2>Hi {first_name}, here is your {month_label} summary for {council_name}</h2>
<div class="info-box">
  <p><strong>Applications received:</strong> {stats.get('applications_received', 0)}</p>
  <p><strong>Applications reviewed:</strong> {stats.get('applications_reviewed', 0)}</p>
  <p><strong>Applications approved:</strong> {stats.get('applications_approved', 0)}</p>
  <p><strong>Total funding awarded:</strong> ${stats.get('funding_awarded', 0):,.0f}</p>
  <p><strong>Active grants:</strong> {stats.get('active_grants', 0)}</p>
  <p><strong>Community votes cast:</strong> {stats.get('votes_cast', 0)}</p>
</div>
<a href="{link}" class="cta-btn">View Full Dashboard &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = (
        f"Hi {first_name},\n\n{month_label} summary for {council_name}:\n"
        f"- Applications received: {stats.get('applications_received', 0)}\n"
        f"- Approved: {stats.get('applications_approved', 0)}\n"
        f"- Funding awarded: ${stats.get('funding_awarded', 0):,.0f}\n\n"
        f"View at: {link}\n\nThe GrantThrive Team"
    )
    return send_email(to_email, subject, html, text)


def send_renewal_reminder(
    to_email: str, first_name: str, council_name: str,
    plan: str, renewal_date: datetime, days_remaining: int
) -> bool:
    subject = f"Your GrantThrive subscription renews in {days_remaining} days"
    renewal_str = renewal_date.strftime('%d %B %Y')
    link = f"{FRONTEND_URL}/portal/council/account-billing"
    plan_label = plan.replace('_', ' ').title()
    html = f"""
<h2>Hi {first_name}, your subscription renews soon</h2>
<p>Your <strong>{plan_label}</strong> subscription for <strong>{council_name}</strong> renews on <strong>{renewal_str}</strong> ({days_remaining} days away).</p>
<p>Please ensure your payment details are up to date to avoid any interruption to your service.</p>
<a href="{link}" class="cta-btn">Review Billing Details &rarr;</a>
<p><strong>The GrantThrive Team</strong></p>"""
    text = f"Hi {first_name},\n\nYour {plan_label} subscription for {council_name} renews on {renewal_str}.\n\nUpdate billing at: {link}\n\nThe GrantThrive Team"
    return send_email(to_email, subject, html, text)
