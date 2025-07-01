# main.py
from fastapi import FastAPI, Query, Depends, HTTPException
from typing import List, Optional
import sqlite3

app = FastAPI()

# Allowed employee columns
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

# DB dependency, opened once per request in the event loop thread
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
