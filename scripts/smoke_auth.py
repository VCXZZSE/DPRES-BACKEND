import json
import uuid
import urllib.error
import urllib.request

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Institution


BASE = "http://127.0.0.1:8001/api/auth"
email = f"student_{uuid.uuid4().hex[:8]}@testcollege.edu"
password = "Password123!"
new_password = "NewPass123!"


def get_test_institution_id() -> int:
    with SessionLocal() as db:
        institution = db.scalar(select(Institution).where(Institution.code == "TESTCOL"))
        if not institution:
            raise RuntimeError("Seed institution TESTCOL not found")
        return institution.id


def call(path, method="GET", payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body) if body else {}
        except Exception:
            parsed = {"raw": body}
        return exc.code, parsed


institution_id = get_test_institution_id()

invalid_status, invalid_body = call(
    "/register-student",
    "POST",
    {
        "email": f"bad_{uuid.uuid4().hex[:6]}@gmail.com",
        "password": password,
        "full_name": "Bad Domain",
        "institution_id": institution_id,
    },
)

reg_status, reg_body = call(
    "/register-student",
    "POST",
    {
        "email": email,
        "password": password,
        "full_name": "Test Student",
        "institution_id": institution_id,
    },
)

login_status, login_body = call("/login-student", "POST", {"email": email, "password": password})
access_token = login_body.get("access_token") if isinstance(login_body, dict) else None

if access_token:
    me_status, me_body = call("/me", "GET", token=access_token)
else:
    me_status, me_body = 0, {"error": "missing token"}

forgot_status, forgot_body = call("/forgot-password", "POST", {"email": email})
reset_token = forgot_body.get("reset_token") if isinstance(forgot_body, dict) else None

if reset_token:
    reset_status, reset_body = call(
        "/reset-password",
        "POST",
        {"token": reset_token, "new_password": new_password},
    )
else:
    reset_status, reset_body = 0, {"error": "missing reset token"}

login2_status, login2_body = call("/login-student", "POST", {"email": email, "password": new_password})

print("register_invalid_domain", invalid_status, invalid_body)
print("register_valid", reg_status, reg_body)
print("login_initial", login_status, {"token_type": login_body.get("token_type") if isinstance(login_body, dict) else None})
print("me", me_status, {"email": me_body.get("email") if isinstance(me_body, dict) else None})
print(
    "forgot",
    forgot_status,
    {
        "message": forgot_body.get("message") if isinstance(forgot_body, dict) else None,
        "has_reset_token": bool(forgot_body.get("reset_token")) if isinstance(forgot_body, dict) else False,
    },
)
print("reset", reset_status, reset_body)
print("login_new_password", login2_status, {"token_type": login2_body.get("token_type") if isinstance(login2_body, dict) else None})
