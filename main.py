# main.py
from fastapi import FastAPI, Query, Depends, HTTPException, Request
from typing import List, Optional
import sqlite3
import time

app = FastAPI()

RATE_LIMIT = 100   # max requests per WINDOW
WINDOW     = 60    # seconds
_counters  = {}    # maps client_ip -> (window_start_ts, count)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client = request.client
    if client is None:
        # fallback to the ASGI scope “client” tuple if needed
        scope_client = request.scope.get("client")
        if isinstance(scope_client, tuple):
            ip = scope_client[0]
        else:
            ip = "0.0.0.0"
    else:
        ip = client.host
    now = time.time()

    start, count = _counters.get(ip, (now, 0))
    # if window has expired, reset
    if now - start > WINDOW:
        start, count = now, 0

    if count >= RATE_LIMIT:
        # too many requests in this WINDOW
        raise HTTPException(status_code=429, detail="Too Many Requests")

    # increment and store
    _counters[ip] = (start, count + 1)
    return await call_next(request)
# ───────────────────────────────────────────────────────────────────────────────

VALID_COLS = {
    "id",
    "organization_id",
    "first_name",
    "last_name",
    "contact_info",
    "department",
    "position",
    "location",
    "status",
    "company",
}

# Dependency to open SQLite in the event‐loop thread
async def get_db():
    conn = sqlite3.connect("employees.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@app.get("/")
async def root():
    return {"message": "Employee Directory API"}

@app.get("/search")
async def search(
    columns: Optional[List[str]]      = Query(None, description="Columns to include"),
    status: Optional[str]             = Query(None),
    location: Optional[str]           = Query(None),
    department: Optional[str]         = Query(None),
    position: Optional[str]           = Query(None),
    company: Optional[str]            = Query(None),
    organization_id: Optional[str]    = Query(None),
    db: sqlite3.Connection            = Depends(get_db),
):
    # Handle dynamic columns
    if columns:
        cols_set = set(columns)
        if not cols_set.issubset(VALID_COLS):
            bad = cols_set - VALID_COLS
            raise HTTPException(
                status_code=400,
                detail=f"Invalid columns requested: {', '.join(bad)}"
            )
        select_clause = ", ".join(columns)
    else:
        select_clause = "*"

    # build filters
    filters = []
    params = []
    for name, val in [
        ("status", status),
        ("location", location),
        ("department", department),
        ("position", position),
        ("company", company),
        ("organization_id", organization_id),
    ]:
        if val is not None:
            filters.append(f"{name} = ?")
            params.append(val)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    sql = f"SELECT {select_clause} FROM employees {where};"

    # Execute and return
    rows = db.execute(sql, params).fetchall()
    return {"results": [dict(r) for r in rows]}
