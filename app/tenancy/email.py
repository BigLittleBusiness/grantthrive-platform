"""
GrantThrive — Tenancy Email Helpers
====================================
Transactional email functions for the council tenancy lifecycle.

In development (MAIL_SUPPRESS_SEND=True or no MAIL_SERVER configured),
all emails are logged to the console instead of being sent.

Requires Flask-Mail to be initialised in the app factory (app/__init__.py).
"""

import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)


def _mail_available() -> bool:
    """Return True if Flask-Mail is initialised and sending is not suppressed."""
    try:
        from flask_mail import Mail
        mail = current_app.extensions.get('mail')
        return mail is not None and not current_app.config.get('MAIL_SUPPRESS_SEND', True)
    except Exception:
        return False


def send_trial_welcome_email(
    to_email: str,
    first_name: str,
    council_name: str,
    portal_url: str,
    trial_ends: datetime,
) -> None:
    """
    Send the welcome email to a new trial council admin.

    If email sending is unavailable (dev mode or missing SMTP config),
    the email content is logged at INFO level instead.

    Args:
        to_email:     Recipient email address.
        first_name:   Recipient's first name for personalisation.
        council_name: The council's display name.
        portal_url:   The council's unique portal URL.
        trial_ends:   UTC datetime when the 14-day trial expires.
    """
    trial_end_str = trial_ends.strftime('%d %B %Y')

    subject = f"Welcome to GrantThrive — Your 14-Day Trial Has Started"

    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to GrantThrive</title>
  <style>
    body {{
      margin: 0; padding: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background-color: #f4f4f5;
      color: #1a2332;
    }}
    .wrapper {{
      max-width: 600px;
      margin: 40px auto;
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }}
    .header {{
      background-color: #15803d;
      padding: 32px 40px;
      text-align: center;
    }}
    .header h1 {{
      color: #ffffff;
      font-size: 24px;
      font-weight: 700;
      margin: 0;
      letter-spacing: -0.3px;
    }}
    .header p {{
      color: #bbf7d0;
      font-size: 14px;
      margin: 6px 0 0;
    }}
    .body {{
      padding: 40px;
    }}
    .body h2 {{
      font-size: 20px;
      font-weight: 700;
      color: #1a2332;
      margin: 0 0 12px;
    }}
    .body p {{
      font-size: 15px;
      line-height: 1.65;
      color: #37474f;
      margin: 0 0 16px;
    }}
    .info-box {{
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 8px;
      padding: 20px 24px;
      margin: 24px 0;
    }}
    .info-box p {{
      margin: 4px 0;
      font-size: 14px;
      color: #166534;
    }}
    .info-box strong {{
      color: #14532d;
    }}
    .cta-btn {{
      display: inline-block;
      background-color: #15803d;
      color: #ffffff !important;
      text-decoration: none;
      font-size: 16px;
      font-weight: 600;
      padding: 14px 32px;
      border-radius: 8px;
      margin: 8px 0 24px;
    }}
    .steps {{
      margin: 24px 0;
    }}
    .step {{
      display: flex;
      align-items: flex-start;
      margin-bottom: 16px;
    }}
    .step-num {{
      background: #15803d;
      color: #fff;
      font-size: 13px;
      font-weight: 700;
      width: 26px;
      height: 26px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-right: 14px;
      margin-top: 2px;
    }}
    .step-text {{
      font-size: 14px;
      color: #37474f;
      line-height: 1.5;
    }}
    .footer {{
      background: #f8fafc;
      border-top: 1px solid #e2e8f0;
      padding: 24px 40px;
      text-align: center;
    }}
    .footer p {{
      font-size: 12px;
      color: #94a3b8;
      margin: 4px 0;
    }}
    .footer a {{
      color: #15803d;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>Welcome to GrantThrive</h1>
      <p>Your grant management platform</p>
    </div>
    <div class="body">
      <h2>Hi {first_name}, your trial is live!</h2>
      <p>
        Thank you for starting a free trial of GrantThrive for
        <strong>{council_name}</strong>. Your portal is ready to use right now.
      </p>

      <div class="info-box">
        <p><strong>Your portal URL:</strong> <a href="{portal_url}" style="color:#15803d;">{portal_url}</a></p>
        <p><strong>Trial expires:</strong> {trial_end_str}</p>
        <p><strong>Your role:</strong> Council Administrator</p>
      </div>

      <a href="{portal_url}" class="cta-btn">Go to Your Portal &rarr;</a>

      <p><strong>Here is what to do next:</strong></p>
      <div class="steps">
        <div class="step">
          <div class="step-num">1</div>
          <div class="step-text">
            <strong>Create your first grant</strong> — Use the Grant Creation Wizard to publish
            a grant in minutes.
          </div>
        </div>
        <div class="step">
          <div class="step-num">2</div>
          <div class="step-text">
            <strong>Invite your team</strong> — Add council staff members from the
            Users section of your dashboard.
          </div>
        </div>
        <div class="step">
          <div class="step-num">3</div>
          <div class="step-text">
            <strong>Customise your branding</strong> — Upload your council logo and set
            your brand colours in Council Settings.
          </div>
        </div>
        <div class="step">
          <div class="step-num">4</div>
          <div class="step-text">
            <strong>Book a demo</strong> — Our team can walk you through the platform
            and answer any questions. <a href="https://www.grantthrive.com/pages/contact.html" style="color:#15803d;">Book a session</a>.
          </div>
        </div>
      </div>

      <p>
        If you have any questions during your trial, reply to this email or visit
        <a href="https://www.grantthrive.com" style="color:#15803d;">grantthrive.com</a>.
      </p>
      <p>
        We are excited to have you on board.<br>
        <strong>The GrantThrive Team</strong>
      </p>
    </div>
    <div class="footer">
      <p>
        &copy; {datetime.now().year} GrantThrive. All rights reserved.
      </p>
      <p>
        <a href="https://www.grantthrive.com/pages/contact.html">Contact Us</a> &middot;
        <a href="https://www.grantthrive.com">grantthrive.com</a>
      </p>
      <p style="margin-top:12px; font-size:11px;">
        You received this email because you signed up for a GrantThrive trial.
      </p>
    </div>
  </div>
</body>
</html>
"""

    text_body = f"""
Welcome to GrantThrive, {first_name}!

Your 14-day free trial for {council_name} has started.

Your portal URL: {portal_url}
Trial expires:   {trial_end_str}
Your role:       Council Administrator

NEXT STEPS:
1. Create your first grant using the Grant Creation Wizard.
2. Invite your team from the Users section.
3. Customise your branding in Council Settings.
4. Book a demo at https://www.grantthrive.com/pages/contact.html

Questions? Reply to this email or visit https://www.grantthrive.com

The GrantThrive Team
"""

    if _mail_available():
        from flask_mail import Message
        from app import mail as flask_mail
        msg = Message(
            subject    = subject,
            recipients = [to_email],
            html       = html_body,
            body       = text_body,
        )
        flask_mail.send(msg)
        logger.info("Trial welcome email sent to %s", to_email)
    else:
        # Dev mode — log the email content instead of sending
        logger.info(
            "DEV MODE — Trial welcome email (not sent):\n"
            "  To:      %s\n"
            "  Subject: %s\n"
            "  Portal:  %s\n"
            "  Expires: %s",
            to_email, subject, portal_url, trial_end_str,
        )
