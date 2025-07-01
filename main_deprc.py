# main.py
from fastapi import FastAPI, Query, Depends
from typing import Optional
import sqlite3
from init_db import populate


app = FastAPI()

def get_db():
    conn = sqlite3.connect("employees.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@app.get("/")
def root():
    return {"message": "Employee Directory API"}

@app.get("/search")
def search(
    status: Optional[str]     = Query(None),
    location: Optional[str]   = Query(None),
    department: Optional[str] = Query(None),
    position: Optional[str]   = Query(None),
    company: Optional[str]    = Query(None),
    organization_id: Optional[str] = Query(None),
    db: sqlite3.Connection    = Depends(get_db),
):
    filters = []
    params  = []

    for name, val in [
        ("status", status),
        ("location", location),
        ("department", department),
        ("position", position),
        ("company", company),
        ("organization_id", organization_id),
    ]:
        if val:
            filters.append(f"{name} = ?")
            params.append(val)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    sql   = f"SELECT * FROM employees {where};"

    rows = db.execute(sql, params).fetchall()
    return {"results": [dict(r) for r in rows]}
