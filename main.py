from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

LICENSES = {}

class LicenseCheck(BaseModel):
    license_key: str
    machine_id: str


@app.post("/check")
def check_license(data: LicenseCheck):
    lic = LICENSES.get(data.license_key)
    if not lic:
        return {"status": "invalid"}

    # 🔒 ilk calisan makineye kilitle
    if lic["machine_id"] is None:
        lic["machine_id"] = data.machine_id

    if lic["machine_id"] != data.machine_id:
        return {"status": "machine_mismatch"}

    if lic["expires_at"] < datetime.utcnow():
        return {"status": "expired"}

    return {
        "status": "ok",
        "expires_at": lic["expires_at"].isoformat()
    }


@app.post("/_admin/add-license")
def add_license(key: str, days: int = 30):
    LICENSES[key] = {
        "machine_id": None,   # ⬅️ otomatik kilit
        "expires_at": datetime.utcnow() + timedelta(days=days)
    }
    return {"status": "added"}
