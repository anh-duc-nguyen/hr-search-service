# init_db.py
import sqlite3
import random
import string
import sys

FIRST_NAMES = [
    "Alex", "Duc", "Anh", "Tim", "Tom", "Tang",
    "Bob", "Candy", "Katy", "Lindy", "Lily", "Karen"
]
LAST_NAMES = [
    "Nguyen", "Tran", "Pham", "Le", "Do", "Nguyen",
    "Tran", "Pham", "Le", "Do"
]
DEPARTMENTS = ["IT", "HR", "Finance", "Marketing", "Sales", "Operations"]
POSITIONS = ["Programmer", "Manager", "Analyst", "Engineer", "Director", "Coordinator"]
LOCATIONS = ["Vietnam", "USA", "Canada", "UK", "Australia", "Germany", "France", "Japan"]
STATUSES = ["Active", "Not Started", "Terminated"]
COMPANIES = ["Acme", "Globex", "Soylent", "Initech", "Umbrella", "Wonka"]
ORGANIZATIONS = ["org1", "org2", "org3", "org4", "org5"]


def create_schema(cursor):
    cursor.execute("""
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
    """)
    # performance indexes
    for col in ["organization_id", "status", "location", "department", "position", "company"]:
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_employees_{col} ON employees({col})"
        )


def random_phone():
    # generate a 10-digit phone number starting with 0
    return "0" + "".join(random.choices(string.digits, k=9))


def random_employee():
    return (
        random.choice(ORGANIZATIONS),
        random.choice(FIRST_NAMES),
        random.choice(LAST_NAMES),
        random_phone(),
        random.choice(DEPARTMENTS),
        random.choice(POSITIONS),
        random.choice(LOCATIONS),
        random.choice(STATUSES),
        random.choice(COMPANIES),
    )


def populate(conn, n):
    cursor = conn.cursor()
    insert_sql = """
        INSERT INTO employees
          (organization_id, first_name, last_name, contact_info,
           department, position, location, status, company)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for _ in range(n):
        cursor.execute(insert_sql, random_employee())
    conn.commit()


def main():
    if len(sys.argv) != 2:
        print(f"Please enter number of rows to insert into db {sys.argv[0]} <number_of_rows>")
        sys.exit(1)

    try:
        n = int(sys.argv[1])
    except ValueError:
        print("Please provide an integer for the number of rows to insert.")
        sys.exit(1)

    conn = sqlite3.connect("employees.db")
    create_schema(conn.cursor())
    populate(conn, n)
    conn.close()
    print(f"Inserted {n} random employee records into employees.db")


if __name__ == "__main__":
    main()