from __future__ import annotations

import argparse
import getpass
import os
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Institution, User, UserRole

DEFAULT_ADMIN_EMAIL = 'admin@sdma.gov.in'
DEFAULT_ADMIN_NAME = 'SDMA Administrator'
DEFAULT_INSTITUTION_CODE = 'SDMA-HQ-001'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Seed or update a single SDMA admin account in Neon/PostgreSQL.'
    )
    parser.add_argument('--email', default=DEFAULT_ADMIN_EMAIL, help='Admin email address')
    parser.add_argument('--password', default=None, help='Admin password (omit to prompt securely)')
    parser.add_argument(
        '--password-env',
        default='SDMA_SEED_PASSWORD',
        help='Environment variable name containing admin password',
    )
    parser.add_argument('--name', default=DEFAULT_ADMIN_NAME, help='Admin full name')
    return parser.parse_args()


def ensure_sdma_institution(db) -> Institution:
    institution = db.scalar(select(Institution).where(Institution.code == DEFAULT_INSTITUTION_CODE))
    if institution:
        return institution

    institution = Institution(
        code=DEFAULT_INSTITUTION_CODE,
        name='State Disaster Management Authority',
        institution_type='college',
        district='Kolkata',
        state='West Bengal',
        allowed_domains=['sdma.gov.in'],
    )
    db.add(institution)
    db.flush()
    return institution


def main() -> None:
    args = parse_args()
    email = args.email.strip().lower()

    password = args.password
    if not password:
        password = os.environ.get(args.password_env)
    if not password:
        password = getpass.getpass('Enter SDMA admin password: ')
    if not password:
        raise ValueError('Password cannot be empty')

    db = SessionLocal()
    try:
        institution = ensure_sdma_institution(db)

        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                full_name=args.name.strip(),
                password_hash=hash_password(password),
                role=UserRole.SDMA_ADMIN,
                institution_id=institution.id,
                is_active=True,
                email_verified_at=datetime.now(timezone.utc),
            )
            db.add(user)
            action = 'created'
        else:
            user.full_name = args.name.strip() or user.full_name
            user.password_hash = hash_password(password)
            user.role = UserRole.SDMA_ADMIN
            user.is_active = True
            user.institution_id = institution.id
            user.email_verified_at = user.email_verified_at or datetime.now(timezone.utc)
            action = 'updated'

        db.commit()
        db.refresh(user)

        print('SDMA admin seeding complete.')
        print(f'  action: {action}')
        print(f'  user_id: {user.id}')
        print(f'  email: {user.email}')
        print(f'  role: {user.role.value}')
        print(f'  institution_id: {user.institution_id}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
