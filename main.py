from fastapi import FastAPI
from datetime import datetime
import hmac, hashlib

app = FastAPI()

SECRET = "SUPER_SECRET_KEY_DEGISTIR"

def sign(data: str) -> str:
    return hmac.new(
        SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

@app.post("/check")
def check_license(data: dict):
    license_key = data.get("license_key")
    machine_id = data.get("machine_id")

    if not license_key or not machine_id:
        return {"status": "error"}

    try:
        expiry, lic_machine, signature = license_key.split("|")
    except ValueError:
        return {"status": "invalid"}

    if lic_machine != machine_id:
        return {"status": "invalid"}

    base = f"{expiry}|{lic_machine}"
    expected = sign(base)

    if not hmac.compare_digest(expected, signature):
        return {"status": "invalid"}

    if datetime.utcnow().date() > datetime.fromisoformat(expiry).date():
        return {"status": "expired"}

    return {
        "status": "ok",
        "expires_at": expiry
    }
