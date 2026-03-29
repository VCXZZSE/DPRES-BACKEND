from sqlalchemy import select

from app.database import SessionLocal
from app.models import Institution


def seed_institution() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(Institution).where(Institution.code == 'TESTCOL'))
        if existing:
            print('Seed skipped: Test College already exists.')
            return

        inst = Institution(
            code='TESTCOL',
            name='Test College',
            institution_type='college',
            district='Kolkata',
            state='West Bengal',
            allowed_domains=['testcollege.edu', 'army.public.edu'],
        )
        db.add(inst)
        db.commit()
        print('Seed complete: Test College inserted.')


if __name__ == '__main__':
    seed_institution()
