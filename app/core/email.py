import smtplib
from datetime import datetime, timedelta, timezone
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


def send_welcome_onboarding_email(to_email: str, user_name: str) -> bool:
    safe_name = (user_name or 'User').strip() or 'User'

    message = EmailMessage()
    message['Subject'] = 'Welcome aboard DPRES'
    message['From'] = settings.SMTP_FROM_EMAIL
    message['To'] = to_email
    message.set_content(
        (
            f'Dear {safe_name},\n\n'
            'Welcome aboard DPRES.\n\n'
            "We're glad to have you join a platform dedicated to strengthening disaster prevention, "
            'preparedness, and response. Your account has been successfully set up.\n\n'
            'With DPRES, you can access essential resources, stay informed, and contribute to proactive '
            'disaster management efforts.\n\n'
            'If you need any assistance or have questions, feel free to reach out to our support team.\n\n'
            'Once again, welcome to DPRES - together, we prepare today to protect tomorrow.\n\n'
            'Warm regards,\n'
            'Team DPRES'
        )
    )
    message.add_alternative(
        f"""
<!doctype html>
<html>
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Welcome aboard DPRES</title>
    </head>
    <body style=\"margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;color:#374151;\">
        <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#f3f4f6;padding:16px 10px;\">
            <tr>
                <td align=\"center\">
                    <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"max-width:680px;background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #e5e7eb;box-shadow:0 12px 26px rgba(15,23,42,0.08);\">
                        <tr>
                            <td style=\"height:6px;background:linear-gradient(90deg,#ea580c,#ffffff,#16a34a);font-size:0;line-height:0;\">&nbsp;</td>
                        </tr>

                        <tr>
                            <td style=\"padding:26px 22px 22px 22px;background:linear-gradient(135deg,#fff7ed,#fef3c7);text-align:center;position:relative;\">
                                <div style=\"display:inline-block;width:66px;height:66px;background:#ffffff;border-radius:999px;box-shadow:0 4px 10px rgba(0,0,0,0.08);line-height:66px;text-align:center;font-size:30px;color:#ea580c;margin-bottom:12px;\">✶</div>
                                <h1 style=\"margin:0 0 8px 0;font-size:24px;line-height:1.3;color:#1f2937;font-weight:700;\">Disaster Preparedness &amp; Response Education System</h1>
                                <div style=\"width:92px;height:4px;border-radius:999px;background:linear-gradient(90deg,#ea580c,#16a34a);margin:0 auto;\"></div>
                            </td>
                        </tr>

                        <tr>
                            <td style=\"padding:24px 22px 22px 22px;\">
                                <p style=\"margin:0 0 14px 0;font-size:17px;line-height:1.6;color:#374151;\">Dear <span style=\"font-weight:700;color:#111827;\">{safe_name}</span>,</p>

                                <p style=\"margin:0 0 14px 0;font-size:24px;line-height:1.35;color:#c2410c;font-weight:600;\">Welcome aboard DPRES.</p>

                                <p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.7;color:#374151;\">We're glad to have you join a platform dedicated to strengthening disaster prevention, preparedness, and response. Your account has been successfully set up, and you are now part of a growing network committed to building safer and more resilient communities.</p>

                                <p style=\"margin:0 0 14px 0;font-size:15px;line-height:1.7;color:#374151;\">With DPRES, you can access essential resources, stay informed, and contribute to proactive disaster management efforts. Every action matters, and your participation plays a crucial role in making a difference.</p>

                                <p style=\"margin:0 0 16px 0;font-size:15px;line-height:1.7;color:#374151;\">If you need any assistance or have questions, feel free to reach out to our support team.</p>

                                <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:linear-gradient(90deg,#fff7ed,#f0fdf4);border-left:4px solid #ea580c;border-radius:8px;\">
                                    <tr>
                                        <td style=\"padding:14px 14px;\">
                                            <p style=\"margin:0;font-size:16px;line-height:1.6;color:#1f2937;font-style:italic;\">Once again, welcome to DPRES - together, we prepare today to protect tomorrow.</p>
                                        </td>
                                    </tr>
                                </table>

                                <p style=\"margin:16px 0 2px 0;font-size:15px;line-height:1.6;color:#1f2937;\">Warm regards,</p>
                                <p style=\"margin:0;font-size:17px;line-height:1.4;color:#111827;font-weight:700;\">Team DPRES</p>
                            </td>
                        </tr>

                        <tr>
                            <td style=\"padding:16px 22px;background:linear-gradient(135deg,#f9fafb,#fff7ed);border-top:1px solid #e5e7eb;text-align:center;\">
                                <p style=\"margin:0 0 4px 0;font-size:12px;line-height:1.5;color:#6b7280;\">Disaster Prevention, Preparedness &amp; Response System</p>
                                <p style=\"margin:0;font-size:11px;line-height:1.5;color:#6b7280;\"><span style=\"color:#ea580c;\">●</span> Building Resilient Communities <span style=\"color:#16a34a;\">●</span></p>
                            </td>
                        </tr>

                        <tr>
                            <td style=\"height:6px;background:linear-gradient(90deg,#ea580c,#ffffff,#16a34a);font-size:0;line-height:0;\">&nbsp;</td>
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


def send_password_changed_alert_email(to_email: str, changed_at_utc: Optional[datetime] = None) -> bool:
    if changed_at_utc is None:
        changed_at_utc = datetime.now(timezone.utc)

    try:
        changed_at_ist = changed_at_utc.astimezone(ZoneInfo('Asia/Kolkata'))
    except Exception:
        # Fallback for minimal Python images that may not include zoneinfo data.
        changed_at_ist = changed_at_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))

    formatted_dt = (
        f"{changed_at_ist.strftime('%A')}, {changed_at_ist.strftime('%B')} "
        f"{changed_at_ist.day}, {changed_at_ist.year} at {changed_at_ist.strftime('%I:%M %p')} IST"
    )

    support_email = 'toshibawin21@gmail.com'
    support_subject = quote('Urgent: Unauthorized DPRES password change', safe='')
    support_body = quote(
        (
            'Hello DPRES Support,\r\n\r\n'
            f'I did not authorize a password change on my account ({to_email}).\r\n'
            f'Password changed at: {formatted_dt}\r\n\r\n'
            'Please help me secure my account immediately.\r\n'
        ),
        safe='',
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
                            <td style="padding:20px 20px 8px 20px;font-size:34px;line-height:1;color:#f97316;text-align:center;">◆</td>
                        </tr>
                        <tr>
                            <td style="padding:0 20px 18px 20px;">
                                <p style="margin:0 0 8px 0;font-size:14px;line-height:1.4;color:#64748b;font-weight:600;text-align:center;letter-spacing:0.4px;">DPRES Password Changed Alert</p>
                                <p style="margin:0 0 12px 0;font-size:36px;line-height:1.1;color:#ef4444;font-weight:700;text-align:center;">PASSWORD CHANGED!</p>
                                <p style="margin:0 0 16px 0;font-size:18px;line-height:1.5;color:#334155;font-weight:600;text-align:left;">Namaste,</p>
                                <p style="margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#334155;">This is to confirm that your password was successfully changed on <span style="color:#c2410c;font-weight:700;">{formatted_dt}</span>.</p>
                                <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;color:#334155;">If you made this change, no further action is required. Your account remains secure.</p>

                                <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#f9f1ef;border-left:6px solid #ef4444;border-radius:10px;\">
                                    <tr>
                                        <td style="padding:18px 14px;">
                                            <p style="margin:0 0 8px 0;font-size:34px;line-height:1;color:#ef4444;text-align:center;">!</p>
                                            <p style="margin:0 0 10px 0;font-size:22px;line-height:1.2;color:#0f172a;font-weight:700;text-align:center;">Was this not you?</p>
                                            <p style="margin:0 0 14px 0;font-size:15px;line-height:1.6;color:#334155;text-align:center;">If you did not make this change, your account may have been compromised. Please contact our support team immediately to secure your account.</p>
                                            <table role=\"presentation\" align=\"center\" cellpadding=\"0\" cellspacing=\"0\" style=\"margin:0 auto;\">
                                                <tr>
                                                    <td align=\"center\" style=\"background:linear-gradient(90deg,#ff6a00,#ff0000);border-radius:16px;\">
                                                        <a href="{support_mailto}" style="display:inline-block;padding:12px 18px;font-size:14px;line-height:1.2;font-weight:700;color:#ffffff;text-decoration:none;">Contact Support Immediately</a>
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


def send_account_removal_email(to_email: str, user_name: Optional[str] = None) -> bool:
    safe_name = (user_name or 'User').strip() or 'User'

    message = EmailMessage()
    message['Subject'] = 'DPRES Account Removal Notice'
    message['From'] = settings.SMTP_FROM_EMAIL
    message['To'] = to_email
    message.set_content(
        (
            f'Dear {safe_name},\n\n'
            'This is to confirm that your DPRES account and associated records have been removed from our system. '
            'Any active sessions have also been revoked.\n\n'
            'If you believe this action was made in error, please contact support immediately.\n\n'
            'Regards,\n'
            'Team DPRES'
        )
    )
    message.add_alternative(
        f"""
<!doctype html>
<html>
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>DPRES Account Removal Notice</title>
    </head>
    <body style=\"margin:0;padding:0;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;color:#111827;\">
        <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#f8fafc;padding:18px 10px;\">
            <tr>
                <td align=\"center\">
                    <table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"max-width:680px;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;\">
                        <tr>
                            <td style=\"height:6px;background:linear-gradient(90deg,#ef4444,#f97316,#facc15);font-size:0;line-height:0;\">&nbsp;</td>
                        </tr>
                        <tr>
                            <td style=\"padding:24px 22px;\">
                                <h1 style=\"margin:0 0 12px 0;font-size:28px;line-height:1.2;color:#b91c1c;text-align:center;\">Account Removal Notice</h1>
                                <p style=\"margin:0 0 12px 0;font-size:16px;line-height:1.6;color:#1f2937;\">Dear <strong>{safe_name}</strong>,</p>
                                <p style=\"margin:0 0 12px 0;font-size:15px;line-height:1.7;color:#374151;\">This is to confirm that your DPRES account and associated records have been removed from our system. Any active sessions have also been revoked.</p>
                                <p style=\"margin:0 0 12px 0;font-size:15px;line-height:1.7;color:#374151;\">If you believe this action was made in error, please contact support immediately.</p>
                                <p style=\"margin:18px 0 0 0;font-size:15px;line-height:1.6;color:#111827;\">Regards,<br/><strong>Team DPRES</strong></p>
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
