from sqlalchemy import select

from app.database import SessionLocal
from app.models import Institution, User, UserRole


def domain(email: str) -> str:
    return email.split('@', 1)[1].strip().lower() if '@' in email else ''


def main() -> None:
    db = SessionLocal()
    try:
        rows = db.execute(
            select(
                User.id,
                User.email,
                User.institution_id,
                Institution.institution_type,
                Institution.allowed_domains,
            )
            .join(Institution, Institution.id == User.institution_id)
            .where(User.role == UserRole.STUDENT)
        ).all()

        offenders: list[tuple[int, str, int, str, list[str]]] = []
        for uid, email, inst_id, inst_type, allowed_domains in rows:
            allowed = [x.strip().lower() for x in (allowed_domains or [])]
            if inst_type != 'college' or domain(email) not in allowed:
                offenders.append((uid, email, inst_id, inst_type, allowed))

        print(f'OFFENDER_COUNT={len(offenders)}')
        for uid, email, inst_id, inst_type, allowed in offenders:
            print(f'{uid}\t{email}\tinst={inst_id}\ttype={inst_type}\tallowed={allowed}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
