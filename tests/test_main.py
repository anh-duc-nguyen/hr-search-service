# tests/test_main.py
import sys
import os

# ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import sqlite3
import pytest
from fastapi.testclient import TestClient

from main import app, get_db

# --- Fixture: in‐memory SQLite DB ---
@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # create schema
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            contact_info TEXT,
            department TEXT,
            position TEXT,
            location TEXT,
            status TEXT,
            company TEXT
        )
    """)
    # insert sample rows
    sample = [
        ("org1", "Alex",  "Nguyen", "0234234510", "IT",      "Programmer", "Vietnam", "Active",      "Acme"),
        ("org1", "Jane",  "Smith",  "0123456789", "HR",      "Manager",    "USA",     "Not Started", "Globex"),
        ("org2", "John",  "Doe",    "0987654321", "Finance", "Analyst",    "Canada",  "Terminated",  "Soylent"),
    ]
    cursor.executemany(
        """
        INSERT INTO employees
          (organization_id, first_name, last_name, contact_info,
           department, position, location, status, company)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sample
    )
    conn.commit()
    yield conn
    conn.close()

# --- Override the get_db dependency to use our in‐memory DB ---
@pytest.fixture(autouse=True)
def override_get_db(db_conn):
    async def _override_get_db():
        yield db_conn
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

# --- Tests ---
def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Employee Directory API"}

def test_search_no_filters():
    resp = client.get("/search")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) == 3

def test_search_status_filter():
    resp = client.get("/search", params={"status": "Active"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["first_name"] == "Alex"

def test_search_multiple_filters():
    resp = client.get("/search", params={"status": "Not Started", "location": "USA"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["last_name"] == "Smith"

def test_search_no_match():
    resp = client.get("/search", params={"status": "Active", "location": "USA"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []

def test_search_no_filters_new():
    resp = client.get("/search")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 3

def test_search_status_filter_new():
    resp = client.get("/search", params={"status": "Active"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["first_name"] == "Alex"

def test_search_company_filter():
    resp = client.get("/search", params={"company": "Globex"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["company"] == "Globex"

def test_select_columns_only():
    resp = client.get(
        "/search",
        params=[("columns", "first_name"), ("columns", "last_name")]
    )
    assert resp.status_code == 200
    data = resp.json()
    # ensure only the two keys are returned
    for item in data["results"]:
        assert set(item.keys()) == {"first_name", "last_name"}
    assert len(data["results"]) == 3

def test_select_columns_and_filter():
    resp = client.get(
        "/search",
        params=[
            ("columns", "first_name"),
            ("columns", "last_name"),
            ("status", "Active")
        ]
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    # exact match on returned dict
    assert data["results"][0] == {"first_name": "Alex", "last_name": "Nguyen"}
