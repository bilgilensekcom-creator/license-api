from fastapi import FastAPI
from datetime import datetime
import sqlite3

app = FastAPI()

def get_db():
    db = sqlite3.connect("licenses.db")
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            license_key TEXT PRIMARY KEY,
            expires_at TEXT
        )
    """)
    db.commit()
    return db

@app.post("/check")
def check_license(data: dict):
    key = data.get("license_key")

    if not key:
        return {"status": "error"}

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT expires_at FROM licenses WHERE license_key=?",
        (key,)
    )
    row = cur.fetchone()

    if not row:
        return {"status": "invalid"}

    expires = datetime.fromisoformat(row[0])

    if expires < datetime.utcnow():
        return {"status": "expired"}

    return {
        "status": "ok",
        "expires_at": row[0]
    }

@app.get("/add-test-license")
def add_test_license():
    from datetime import timedelta

    key = "TEST-LISANS-123"
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO licenses VALUES (?,?)",
        (key, expires)
    )
    db.commit()

    return {
        "status": "added",
        "license_key": key,
        "expires_at": expires
    }
