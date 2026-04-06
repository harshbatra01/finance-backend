"""
Database seeding script.

Populates the database with realistic sample data for development and testing.
Creates one user per role and ~30 financial records spanning several months
to demonstrate filtering, aggregation, and trend features.

Usage:
    python seed.py

The script is idempotent — it checks for existing data before seeding
and will skip if the database already contains records.
"""

import random
from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole
from app.models.record import FinancialRecord, RecordType


def seed_database():
    """Populate the database with sample users and financial records."""
    app = create_app()

    with app.app_context():
        # Check if data already exists
        if User.query.count() > 0:
            print("Database already contains data. Skipping seed.")
            print(f"  Users: {User.query.count()}")
            print(f"  Records: {FinancialRecord.query.count()}")
            return

        print("Seeding database...")

        # --- Create sample users (one per role) ---
        users = _create_users()
        db.session.add_all(users)
        db.session.flush()  # Assign IDs before creating records

        admin_user = next(u for u in users if u.role == UserRole.ADMIN)

        # --- Create sample financial records ---
        records = _create_financial_records(admin_user.id)
        db.session.add_all(records)

        db.session.commit()

        print(f"  Created {len(users)} users:")
        for user in users:
            print(f"    - {user.email} (role: {user.role.value}, password: 'password123')")
        print(f"  Created {len(records)} financial records")
        print("\nSeed complete! You can now log in with any of the above accounts.")


def _create_users():
    """Create sample users with different roles."""
    users_data = [
        {
            "email": "admin@example.com",
            "name": "Alice Admin",
            "role": UserRole.ADMIN,
            "password": "password123",
        },
        {
            "email": "analyst@example.com",
            "name": "Bob Analyst",
            "role": UserRole.ANALYST,
            "password": "password123",
        },
        {
            "email": "viewer@example.com",
            "name": "Charlie Viewer",
            "role": UserRole.VIEWER,
            "password": "password123",
        },
    ]

    users = []
    for data in users_data:
        user = User(
            email=data["email"],
            name=data["name"],
                role=data["role"],
        )
        user.set_password(data["password"])
        users.append(user)

    return users


def _create_financial_records(created_by_user_id):
    """
    Create realistic sample financial records spanning the last 6 months.

    Generates a mix of income and expense records across various categories
    with realistic amounts and dates.
    """
    today = date.today()

    # Define realistic income entries
    income_entries = [
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5200.00, "description": "Monthly salary (raise)"},
        {"category": "Freelance", "amount": 1500.00, "description": "Web development project"},
        {"category": "Freelance", "amount": 800.00, "description": "Logo design work"},
        {"category": "Freelance", "amount": 2200.00, "description": "Consulting engagement"},
        {"category": "Investment", "amount": 350.00, "description": "Dividend payout"},
        {"category": "Investment", "amount": 420.00, "description": "Interest earnings"},
        {"category": "Other", "amount": 150.00, "description": "Cash gift received"},
    ]

    # Define realistic expense entries
    expense_entries = [
        {"category": "Rent", "amount": 1500.00, "description": "Apartment rent"},
        {"category": "Rent", "amount": 1500.00, "description": "Apartment rent"},
        {"category": "Rent", "amount": 1500.00, "description": "Apartment rent"},
        {"category": "Rent", "amount": 1500.00, "description": "Apartment rent"},
        {"category": "Rent", "amount": 1500.00, "description": "Apartment rent"},
        {"category": "Rent", "amount": 1500.00, "description": "Apartment rent"},
        {"category": "Utilities", "amount": 180.00, "description": "Electricity and water"},
        {"category": "Utilities", "amount": 95.00, "description": "Internet bill"},
        {"category": "Utilities", "amount": 65.00, "description": "Phone bill"},
        {"category": "Groceries", "amount": 420.00, "description": "Weekly grocery shopping"},
        {"category": "Groceries", "amount": 380.00, "description": "Weekly grocery shopping"},
        {"category": "Groceries", "amount": 350.00, "description": "Weekly grocery shopping"},
        {"category": "Transport", "amount": 120.00, "description": "Monthly transit pass"},
        {"category": "Transport", "amount": 45.00, "description": "Uber rides"},
        {"category": "Healthcare", "amount": 250.00, "description": "Doctor visit"},
        {"category": "Healthcare", "amount": 85.00, "description": "Pharmacy"},
        {"category": "Entertainment", "amount": 15.99, "description": "Netflix subscription"},
        {"category": "Entertainment", "amount": 65.00, "description": "Concert tickets"},
        {"category": "Education", "amount": 199.00, "description": "Online course"},
        {"category": "Shopping", "amount": 350.00, "description": "New running shoes"},
        {"category": "Shopping", "amount": 89.00, "description": "Books"},
        {"category": "Insurance", "amount": 200.00, "description": "Health insurance premium"},
        {"category": "Taxes", "amount": 950.00, "description": "Quarterly tax payment"},
    ]

    records = []

    # Assign dates spread across the last 6 months
    random.seed(42)  # Fixed seed for reproducible demo data

    for entry in income_entries:
        days_ago = random.randint(0, 180)
        record_date = today - timedelta(days=days_ago)
        records.append(
            FinancialRecord(
                amount=entry["amount"],
                type=RecordType.INCOME,
                category=entry["category"],
                date=record_date,
                description=entry["description"],
                created_by=created_by_user_id,
            )
        )

    for entry in expense_entries:
        days_ago = random.randint(0, 180)
        record_date = today - timedelta(days=days_ago)
        records.append(
            FinancialRecord(
                amount=entry["amount"],
                type=RecordType.EXPENSE,
                category=entry["category"],
                date=record_date,
                description=entry["description"],
                created_by=created_by_user_id,
            )
        )

    return records


if __name__ == "__main__":
    seed_database()
