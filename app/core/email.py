import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional
from urllib.parse import quote
from zoneinfo import ZoneInfo

from app.core.config import settings


def _build_token_email_html(title: str, subtitle: str, token: str, note: str) -> str:
    # Use table-based layout and inline CSS for broad email-client compatibility.
    return f"""
<!doctype html>
<html>
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>{title}</title>
    </head>
    <body style=\"margin:0;padding:0;background:#edf1f7;font-family:Arial,Helvetica,sans-serif;color:#111827;\">
        <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#edf1f7;padding:16px 10px;\">
            <tr>
                <td align=\"center\">
                    <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"max-width:680px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #dbe3ef;\">
                        <tr>
                            <td style=\"height:6px;background:linear-gradient(90deg,#0f4fbf,#0ea5e9,#16a34a);font-size:0;line-height:0;\">&nbsp;</td>
                        </tr>
                        <tr>
                            <td style=\"padding:20px 28px 16px 28px;\">
                                <div style=\"text-align:center;\">
                                    <div style=\"font-size:40px;line-height:1;margin:0 0 10px 0;\">🦚</div>
                                    <h1 style=\"margin:0 0 12px 0;font-size:34px;line-height:1.2;color:#0f285f;font-weight:700;text-align:center;\">{title}</h1>
                                    <p style=\"margin:0 0 16px 0;font-size:17px;line-height:1.45;color:#374151;text-align:center;\">{subtitle}</p>
                                </div>

                                <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#f3f8ff;border:1px solid #d7e6ff;border-radius:12px;\">
                                    <tr>
                                        <td align=\"center\" style=\"padding:18px 16px 16px 16px;\">
                                            <div style=\"font-size:15px;color:#4b5563;margin-bottom:8px;text-align:center;\">Your verification code</div>
                                            <div style=\"font-family:'Courier New',monospace;font-size:44px;line-height:1.1;letter-spacing:8px;font-weight:700;color:#102a63;text-align:center;\">{token}</div>
                                        </td>
                                    </tr>
                                </table>

                                <p style=\"margin:14px 0 0 0;font-size:14px;line-height:1.45;color:#4b5563;text-align:center;\">{note}</p>
                                <p style=\"margin:8px 0 0 0;font-size:13px;line-height:1.4;color:#6b7280;text-align:center;\">For your security, never share this code with anyone.</p>
                            </td>
                        </tr>
                        <tr>
                            <td style=\"padding:12px 28px;background:#f8fafc;border-top:1px solid #e5e7eb;font-size:12px;line-height:1.4;color:#64748b;text-align:center;\">
                                DPRES Secure Access • This is an automated email
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
</html>
"""


def _send_email(message: EmailMessage) -> bool:
    if not settings.smtp_enabled:
        return False

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)

    return True


def send_signup_verification_email(to_email: str, token: str) -> bool:
    message = EmailMessage()
    message['Subject'] = 'DPRES Signup Verification'
    message['From'] = settings.SMTP_FROM_EMAIL
    message['To'] = to_email
    message.set_content(
        (
            "Let's get you signed in\n\n"
            'Use this verification code to complete your DPRES signup:\n\n'
            f'{token}\n\n'
            'This code is valid for 15 minutes.'
        )
    )
    message.add_alternative(
        _build_token_email_html(
            title="Let's get you signed in",
            subtitle='Use this code to complete your DPRES signup.',
            token=token,
            note='Please note this code is only valid for 15 minutes.',
        ),
        subtype='html',
    )

    return _send_email(message)


def send_password_reset_token_email(to_email: str, token: str) -> bool:
    message = EmailMessage()
    message['Subject'] = 'DPRES Password Reset Verification'
    message['From'] = settings.SMTP_FROM_EMAIL
    message['To'] = to_email
    message.set_content(
        (
            'We received a request to reset your DPRES password.\n\n'
            'Use the verification token below to reset your password:\n\n'
            f'{token}\n\n'
            'This token expires in 15 minutes.\n\n'
            'If you did not request this reset, you can ignore this email.'
        )
    )
    message.add_alternative(
        _build_token_email_html(
            title='Password reset request',
            subtitle='Use this code to reset your DPRES password.',
            token=token,
            note='Please note this code is only valid for 15 minutes. If this was not you, ignore this email.',
        ),
        subtype='html',
    )

    return _send_email(message)


def send_password_changed_alert_email(to_email: str, changed_at_utc: Optional[datetime] = None) -> bool:
    if changed_at_utc is None:
        changed_at_utc = datetime.now(timezone.utc)
    changed_at_ist = changed_at_utc.astimezone(ZoneInfo('Asia/Kolkata'))
    formatted_dt = (
        f"{changed_at_ist.strftime('%A')}, {changed_at_ist.strftime('%B')} "
        f"{changed_at_ist.day}, {changed_at_ist.year} at {changed_at_ist.strftime('%I:%M %p')} IST"
    )

    support_email = 'toshibawin21@gmail.com'
    support_subject = quote('Urgent: Unauthorized DPRES password change')
    support_body = quote(
        (
            'Hello DPRES Support,%0D%0A%0D%0A'
            f'I did not authorize a password change on my account ({to_email}).%0D%0A'
            f'Password changed at: {formatted_dt}%0D%0A%0D%0A'
            'Please help me secure my account immediately.%0D%0A'
        )
    )
    support_mailto = f'mailto:{support_email}?subject={support_subject}&body={support_body}'

    message = EmailMessage()
    message['Subject'] = 'DPRES Password Changed Alert'
    message['From'] = settings.SMTP_FROM_EMAIL
    message['To'] = to_email
    message.set_content(
        (
            'Namaste,\n\n'
            f'This is to confirm that your password was successfully changed on {formatted_dt}.\n\n'
            'If you made this change, no further action is required. Your account remains secure.\n\n'
            'If this was not you, please contact support immediately:\n'
            f'{support_email}'
        )
    )
    message.add_alternative(
        f"""
<!doctype html>
<html>
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>DPRES Password Changed Alert</title>
    </head>
    <body style=\"margin:0;padding:0;background:#f4efe6;font-family:Arial,Helvetica,sans-serif;color:#334155;\">
        <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#f4efe6;padding:16px 10px;\">
            <tr>
                <td align=\"center\">
                    <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"max-width:760px;background:#eef1f5;border:1px solid #f0a55d;border-radius:14px;overflow:hidden;\">
                        <tr>
                            <td style=\"padding:28px 24px 10px 24px;font-size:46px;line-height:1;color:#f97316;text-align:center;\">◆</td>
                        </tr>
                        <tr>
                            <td style=\"padding:0 24px 22px 24px;\">
                                <p style=\"margin:0 0 16px 0;font-size:44px;line-height:1.1;color:#ef4444;font-weight:700;text-align:center;\">PASSWORD CHANGED!</p>
                                <p style=\"margin:0 0 20px 0;font-size:17px;line-height:1.6;color:#334155;text-align:center;\">Namaste,</p>
                                <p style=\"margin:0 0 18px 0;font-size:17px;line-height:1.65;color:#334155;\">This is to confirm that your password was successfully changed on <span style=\"color:#c2410c;font-weight:700;\">{formatted_dt}</span>.</p>
                                <p style=\"margin:0 0 20px 0;font-size:17px;line-height:1.65;color:#334155;\">If you made this change, no further action is required. Your account remains secure.</p>

                                <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#f9f1ef;border-left:6px solid #ef4444;border-radius:10px;\">
                                    <tr>
                                        <td style=\"padding:22px 18px;\">
                                            <p style=\"margin:0 0 12px 0;font-size:46px;line-height:1;color:#ef4444;text-align:center;\">!</p>
                                            <p style=\"margin:0 0 12px 0;font-size:44px;line-height:1.1;color:#0f172a;font-weight:700;text-align:center;\">Was this not you?</p>
                                            <p style=\"margin:0 0 18px 0;font-size:17px;line-height:1.65;color:#334155;text-align:center;\">If you did not make this change, your account may have been compromised. Please contact our support team immediately to secure your account.</p>
                                            <table role=\"presentation\" align=\"center\" cellpadding=\"0\" cellspacing=\"0\" style=\"margin:0 auto;\">
                                                <tr>
                                                    <td align=\"center\" style=\"background:linear-gradient(90deg,#ff6a00,#ff0000);border-radius:16px;\">
                                                        <a href=\"{support_mailto}\" style=\"display:inline-block;padding:14px 22px;font-size:16px;line-height:1.2;font-weight:700;color:#ffffff;text-decoration:none;\">Contact Support Immediately</a>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style=\"padding:14px 24px;background:#f8fafc;border-top:1px solid #e2e8f0;font-size:12px;line-height:1.45;color:#64748b;text-align:center;\">
                                DPRES Secure Access • This is an automated email
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
</html>
        """,
        subtype='html',
    )

    return _send_email(message)
