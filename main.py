import os
from datetime import datetime, timedelta, timezone

import psycopg2
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# =========================
# STATIC SITE
# =========================
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")


# =========================
# ENV
# =========================
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

ADMIN_SECRET = os.getenv("ADMIN_SECRET")


# =========================
# DB
# =========================
def get_conn():
    if not all([DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT]):
        raise HTTPException(status_code=500, detail="DB env vars missing")

    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME,
        port=DB_PORT,
        sslmode="require",
    )
    conn.autocommit = True
    return conn


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS licenses (
              license_key TEXT PRIMARY KEY,
              machine_id TEXT,
              expires_at TIMESTAMPTZ NOT NULL
            );
            """
        )


# =========================
# HELPERS
# =========================
def utcnow():
    return datetime.now(timezone.utc)


def get_license(key: str):
    conn = get_conn()
    ensure_table(conn)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT license_key, machine_id, expires_at FROM licenses WHERE license_key=%s",
            (key,),
        )
        row = cur.fetchone()

    conn.close()
    if not row:
        return None

    return {
        "license_key": row[0],
        "machine_id": row[1],
        "expires_at": row[2],
    }


def bind_machine(key: str, machine_id: str):
    conn = get_conn()
    ensure_table(conn)

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE licenses SET machine_id=%s WHERE license_key=%s",
            (machine_id, key),
        )

    conn.close()


def upsert_license(key: str, days: int):
    conn = get_conn()
    ensure_table(conn)

    expires = utcnow() + timedelta(days=days)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO licenses (license_key, machine_id, expires_at)
            VALUES (%s, NULL, %s)
            ON CONFLICT (license_key)
            DO UPDATE SET machine_id=NULL, expires_at=EXCLUDED.expires_at
            """,
            (key, expires),
        )

    conn.close()
    return expires


# =========================
# ADMIN AUTH
# =========================
def admin_auth(x_admin_key: str = Header(default=None)):
    if not ADMIN_SECRET:
        raise HTTPException(status_code=500, detail="ADMIN_SECRET missing")

    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


# =========================
# MODELS
# =========================
class LicenseCheck(BaseModel):
    license_key: str
    machine_id: str


# =========================
# PUBLIC API
# =========================
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

    return {"status": "ok", "expires_at": lic["expires_at"].isoformat()}


# =========================
# ADMIN API
# =========================
@app.post("/_admin/add-license", dependencies=[Depends(admin_auth)])
def add_license(key: str, days: int = 30):
    if not key or not key.strip():
        return {"status": "invalid_key"}

    if days <= 0:
        return {"status": "invalid_days"}

    expires = upsert_license(key.strip(), days)
    return {"status": "added", "expires_at": expires.isoformat()}

@app.post("/_admin/delete", dependencies=[Depends(admin_auth)])
def delete_license(key: str):
    conn = get_conn()
    ensure_table(conn)

    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM licenses WHERE license_key=%s",
            (key,),
        )

        if cur.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="License not found")

    conn.close()
    return {"status": "deleted", "key": key}



@app.get("/_admin/list", dependencies=[Depends(admin_auth)])
def list_licenses():
    conn = get_conn()
    ensure_table(conn)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT license_key, machine_id, expires_at FROM licenses ORDER BY expires_at DESC"
        )
        rows = cur.fetchall()

    conn.close()

    return [
        {
            "license_key": r[0],
            "machine_id": r[1],
            "expires_at": r[2].isoformat(),
        }
        for r in rows
    ]

