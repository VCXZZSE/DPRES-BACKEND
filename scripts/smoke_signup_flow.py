import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def req(method: str, path: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(BASE + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8") or "{}"
            return response.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") or "{}"
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return exc.code, parsed


email = "student001@edu.in"

init_status, init_body = req(
    "POST",
    "/api/auth/signup-initiate",
    {
        "institution_id": 1,
        "email": email,
        "id_card_number": "IDCARD-001",
        "full_name": "Repome Test",
        "age": 19,
    },
)
print("signup-initiate", init_status, init_body)

token = init_body.get("verification_token", "") if isinstance(init_body, dict) else ""

if token:
    verify_status, verify_body = req("POST", "/api/auth/verify-email", {"token": token})
else:
    verify_status, verify_body = 0, {"detail": "missing token"}
print("verify-email", verify_status, verify_body)

if token:
    complete_status, complete_body = req(
        "POST",
        "/api/auth/complete-signup",
        {"token": token, "password": "Password123!"},
    )
else:
    complete_status, complete_body = 0, {"detail": "missing token"}
print("complete-signup", complete_status, complete_body)

login_status, login_body = req(
    "POST",
    "/api/auth/login-student",
    {"email": email, "password": "Password123!"},
)
print(
    "login-student",
    login_status,
    {
        "has_access_token": bool(login_body.get("access_token")) if isinstance(login_body, dict) else False,
        "detail": login_body.get("detail") if isinstance(login_body, dict) else None,
    },
)
