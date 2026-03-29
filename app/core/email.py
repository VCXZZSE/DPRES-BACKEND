import smtplib
from email.message import EmailMessage

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


def send_password_changed_alert_email(to_email: str) -> bool:
    # Reserved for your upcoming custom template design handoff.
    # Keeping this as a simple fallback mail for now.
    message = EmailMessage()
    message['Subject'] = 'DPRES Password Changed Alert'
    message['From'] = settings.SMTP_FROM_EMAIL
    message['To'] = to_email
    message.set_content(
        (
            'Your DPRES password was changed successfully.\n\n'
            'If you made this change, no action is required.\n\n'
            'If you did NOT make this change, please contact us immediately at support@dpres.local.'
        )
    )

    return _send_email(message)
