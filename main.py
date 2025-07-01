# main.py
from fastapi import FastAPI, Query, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse, HTMLResponse
from typing import List, Optional
import sqlite3
import time

app = FastAPI(
    title="HR Employee Search Service",
    description="Employee search API with per-organization isolation",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

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
        # raise HTTPException(status_code=429, detail="Too Many Requests")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too Many Requests"}
        )

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

# @app.get("/")
# async def root():
#     return {"message": "Employee Directory API"}

@app.get("/", response_class=HTMLResponse)
async def ui():
    return """
    <!-- This is AI stuff. I can't code HTML please just don't force me to code html -->
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Employee Directory Search</title>
    </head>
    <body style="font-family:sans-serif; padding:2rem;">
      <h1>🔍 Employee Directory</h1>
      <form id="searchForm">
        <label>Status: <input name="status" /></label><br/>
        <label>Location: <input name="location" /></label><br/>
        <label>Department: <input name="department" /></label><br/>
        <label>Position: <input name="position" /></label><br/>
        <label>Company: <input name="company" /></label><br/>
        <label>Organization ID: <input name="organization_id" /></label><br/>
        <button type="submit">Search</button>
      </form>
      <pre id="results" style="background:#f4f4f4; padding:1rem; margin-top:1rem;"></pre>
      <script>
        const form = document.getElementById('searchForm');
        const out  = document.getElementById('results');
        form.addEventListener('submit', async e => {
          e.preventDefault();
          const params = new URLSearchParams(
            Array.from(new FormData(form).entries())
              .filter(([_, v]) => v)
          );
          const res = await fetch('/search?' + params, {
            headers: { 'X-Organization-ID': document.querySelector('input[name="organization_id"]').value }
          });
          const data = await res.json();
          out.textContent = JSON.stringify(data, null, 2);
        });
      </script>
    </body>
    </html>
    """

@app.get("/search")
async def search(
    x_org_id: str                   = Header(..., alias="X-Organization-ID"),
    columns: Optional[List[str]]    = Query(None, description="Columns to include"),
    status: Optional[str]           = Query(None),
    location: Optional[str]         = Query(None),
    department: Optional[str]       = Query(None),
    position: Optional[str]         = Query(None),
    company: Optional[str]          = Query(None),
    db: sqlite3.Connection          = Depends(get_db),
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

    filters = ["organization_id = ?"]
    params = [x_org_id]
    for name, val in [
        ("status", status),
        ("location", location),
        ("department", department),
        ("position", position),
        ("company", company),
        # ("organization_id", organization_id),
    ]:
        if val is not None:
            filters.append(f"{name} = ?")
            params.append(val)

    where = f"WHERE {' AND '.join(filters)}"
    sql = f"SELECT {select_clause} FROM employees {where};"
    rows = db.execute(sql, params).fetchall()
    return {"results": [dict(r) for r in rows]}
