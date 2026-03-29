from datetime import datetime, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Institution, StudentDirectory, User, UserRole

DEV_EMAIL = 'developer@edu.in'
DEV_PASSWORD = 'DevPass@123'
DEV_FULL_NAME = 'Developer Access'
DEV_ID_CARD = 'DEV-0001'
DEV_INSTITUTION_CODE = 'DEV-COL-001'


def main() -> None:
    db = SessionLocal()
    try:
        institution = db.scalar(select(Institution).where(Institution.code == DEV_INSTITUTION_CODE))
        if not institution:
            institution = Institution(
                code=DEV_INSTITUTION_CODE,
                name='Developer Test College',
                institution_type='college',
                district='Kolkata',
                state='West Bengal',
                allowed_domains=['edu.in'],
            )
            db.add(institution)
            db.flush()

        user = db.scalar(select(User).where(User.email == DEV_EMAIL))
        if not user:
            user = User(
                email=DEV_EMAIL,
                id_card_number=DEV_ID_CARD,
                full_name=DEV_FULL_NAME,
                password_hash=hash_password(DEV_PASSWORD),
                role=UserRole.STUDENT,
                institution_id=institution.id,
                is_active=True,
                email_verified_at=datetime.now(timezone.utc),
            )
            db.add(user)
        else:
            user.password_hash = hash_password(DEV_PASSWORD)
            user.full_name = DEV_FULL_NAME
            user.is_active = True
            user.email_verified_at = user.email_verified_at or datetime.now(timezone.utc)
            if not user.institution_id:
                user.institution_id = institution.id
            if not user.id_card_number:
                user.id_card_number = DEV_ID_CARD

        directory_entry = db.scalar(
            select(StudentDirectory).where(
                StudentDirectory.email == DEV_EMAIL,
            )
        )
        if not directory_entry:
            db.add(
                StudentDirectory(
                    institution_id=institution.id,
                    email=DEV_EMAIL,
                    id_card_number=DEV_ID_CARD,
                    full_name=DEV_FULL_NAME,
                    age=20,
                    is_active=True,
                )
            )

        db.commit()

        print('Developer login is ready:')
        print(f'  email: {DEV_EMAIL}')
        print(f'  password: {DEV_PASSWORD}')
        print(f'  institution_id: {institution.id}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
