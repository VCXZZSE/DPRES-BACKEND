from __future__ import annotations

import argparse

from sqlalchemy import select

from app.core.email import send_account_removal_email
from app.database import SessionLocal
from app.models import EmailVerification, PasswordReset, SessionToken, SignupVerification, StudentDirectory, User


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Delete a user account and related records by email.')
    parser.add_argument('--email', required=True, help='User email to remove')
    parser.add_argument(
        '--skip-email',
        action='store_true',
        help='Skip sending the account removal notification email',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    email = args.email.strip().lower()

    db = SessionLocal()
    summary: dict[str, int | bool | str | None] = {
        'email': email,
        'user_id': None,
        'user_deleted': False,
        'sessions_deleted': 0,
        'password_resets_deleted': 0,
        'email_verifications_deleted': 0,
        'signup_verifications_deleted': 0,
        'student_directory_deleted': 0,
        'notification_email_sent': False,
    }

    try:
        user = db.scalar(select(User).where(User.email == email))
        user_name = user.full_name if user else None

        if user:
            summary['user_id'] = user.id
            summary['sessions_deleted'] = (
                db.query(SessionToken).filter(SessionToken.user_id == user.id).delete(synchronize_session=False)
            )
            summary['password_resets_deleted'] = (
                db.query(PasswordReset).filter(PasswordReset.user_id == user.id).delete(synchronize_session=False)
            )
            summary['email_verifications_deleted'] = (
                db.query(EmailVerification)
                .filter(EmailVerification.user_id == user.id)
                .delete(synchronize_session=False)
            )

            db.delete(user)
            summary['user_deleted'] = True

        summary['signup_verifications_deleted'] = (
            db.query(SignupVerification).filter(SignupVerification.email == email).delete(synchronize_session=False)
        )
        summary['student_directory_deleted'] = (
            db.query(StudentDirectory).filter(StudentDirectory.email == email).delete(synchronize_session=False)
        )

        db.commit()

        if not args.skip_email:
            try:
                summary['notification_email_sent'] = send_account_removal_email(email, user_name)
            except Exception:
                summary['notification_email_sent'] = False

        print('User account removal complete.')
        for key, value in summary.items():
            print(f'  {key}: {value}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
