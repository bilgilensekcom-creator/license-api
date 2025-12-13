import os
from datetime import datetime, timedelta, timezone

import psycopg2
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI()

# -------------------------
# ENV
# -------------------------
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

ADMIN_SECRET = os.getenv("ADMIN_SECRET")


# -------------------------
# DB CONNECT
# -------------------------
def get_conn():
    if not all([DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT]):
        raise RuntimeError("Missing DB env vars")
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME,
        port=DB_PORT,
        sslmode="require",
    )


conn = get_conn()
conn.autocommit = True


def ensure_table():
    with conn.cursor() as cur:
        cur.execute(
            """
            create table if not exists licenses (
              license_key text primary key,
              machine_id text,
              expires_at timestamptz not null
            );
            """
        )


ensure_table()


# -------------------------
# HELPERS
# -------------------------
def utcnow():
    return datetime.now(timezone.utc)


def get_license(key: str):
    with conn.cursor() as cur:
        cur.execute(
            "select license_key, machine_id, expires_at from licenses where license_key=%s",
            (key,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"license_key": row[0], "machine_id": row[1], "expires_at": row[2]}


def bind_machine(key: str, machine_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "update licenses set machine_id=%s where license_key=%s",
            (machine_id, key),
        )


def upsert_license(key: str, days: int):
    expires = utcnow() + timedelta(days=days)
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into licenses (license_key, machine_id, expires_at)
            values (%s, null, %s)
            on conflict (license_key)
            do update set machine_id=null, expires_at=excluded.expires_at
            """,
            (key, expires),
        )
    return expires


# -------------------------
# ADMIN AUTH
# -------------------------
def admin_auth(x_admin_key: str = Header(default=None)):
    if not ADMIN_SECRET:
        raise HTTPException(status_code=500, detail="ADMIN_SECRET missing on server")
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


# -------------------------
# API
# -------------------------
class LicenseCheck(BaseModel):
    license_key: str
    machine_id: str


@app.post("/check")
def check_license(data: LicenseCheck):
    lic = get_license(data.license_key)
    if not lic:
        return {"status": "invalid"}

    if lic["machine_id"] is None:
        bind_machine(data.license_key, data.machine_id)
        lic["machine_id"] = data.machine_id

    if lic["machine_id"] != data.machine_id:
        return {"status": "machine_mismatch"}

    if lic["expires_at"] < utcnow():
        return {"status": "expired"}

    return {
        "status": "ok",
        "expires_at": lic["expires_at"].isoformat(),
    }


@app.post("/_admin/add-license", dependencies=[Depends(admin_auth)])
def add_license(key: str, days: int = 30):
    if not key or not key.strip():
        return {"status": "invalid_key"}
    if days <= 0:
        return {"status": "invalid_days"}

    expires = upsert_license(key.strip(), days)
    return {"status": "added", "expires_at": expires.isoformat()}
