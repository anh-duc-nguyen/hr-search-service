# init_db.py
import sqlite3

def main():
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    # create table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
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
        """
    )
    # performance indexes
    for col in ["organization_id", "status", "location", "department", "position", "company"]:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_employees_{col} ON employees({col})")

    # insert sample data
    cursor.execute(
        """
        INSERT INTO employees (organization_id, first_name, last_name, contact_info, department, position, location, status, company)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("org1", "Alex", "Nguyen", "0234234510", "IT", "Programmer", "Vietnam", "Active", "Acme"),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()