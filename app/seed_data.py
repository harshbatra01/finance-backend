"""
Seed data helpers.

Render's free plan may not support one-off shells. To keep the project easy to
demo, we support optional auto-seeding on app startup (guarded by env var and
idempotent checks).
"""

from __future__ import annotations

import os
import random
from datetime import date, timedelta
from typing import Tuple

from app.extensions import db
from app.models.user import User, UserRole
from app.models.record import FinancialRecord, RecordType


DEFAULT_SEED_PASSWORD = os.getenv("SEED_PASSWORD", "password123")


def seed_if_empty() -> Tuple[int, int]:
    """
    Seed the database only if it has no users yet.

    Returns:
        (users_created, records_created)
    """
    if User.query.count() > 0:
        return 0, 0

    users = _create_users()
    db.session.add_all(users)
    db.session.flush()

    admin_user = next(u for u in users if u.role == UserRole.ADMIN)
    records = _create_financial_records(admin_user.id)
    db.session.add_all(records)
    db.session.commit()

    return len(users), len(records)


def _create_users():
    users_data = [
        {
            "email": "admin@example.com",
            "name": "Alice Admin",
            "role": UserRole.ADMIN,
        },
        {
            "email": "analyst@example.com",
            "name": "Bob Analyst",
            "role": UserRole.ANALYST,
        },
        {
            "email": "viewer@example.com",
            "name": "Charlie Viewer",
            "role": UserRole.VIEWER,
        },
    ]

    users = []
    for data in users_data:
        user = User(email=data["email"], name=data["name"], role=data["role"])
        user.set_password(DEFAULT_SEED_PASSWORD)
        users.append(user)

    return users


def _create_financial_records(created_by_user_id: str):
    today = date.today()

    income_entries = [
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5000.00, "description": "Monthly salary"},
        {"category": "Salary", "amount": 5200.00, "description": "Monthly salary (raise)"},
        {"category": "Freelance", "amount": 1500.00, "description": "Web project"},
        {"category": "Freelance", "amount": 2200.00, "description": "Consulting"},
        {"category": "Investment", "amount": 350.00, "description": "Dividend payout"},
        {"category": "Other", "amount": 150.00, "description": "Cash gift"},
    ]

    expense_entries = [
        {"category": "Rent", "amount": 1500.00, "description": "Apartment rent"},
        {"category": "Rent", "amount": 1500.00, "description": "Apartment rent"},
        {"category": "Utilities", "amount": 180.00, "description": "Electricity & water"},
        {"category": "Groceries", "amount": 420.00, "description": "Groceries"},
        {"category": "Transport", "amount": 120.00, "description": "Transit pass"},
        {"category": "Healthcare", "amount": 250.00, "description": "Doctor visit"},
        {"category": "Entertainment", "amount": 15.99, "description": "Subscription"},
        {"category": "Education", "amount": 199.00, "description": "Online course"},
        {"category": "Taxes", "amount": 950.00, "description": "Quarterly tax"},
    ]

    records = []
    random.seed(42)

    for entry in income_entries:
        record_date = today - timedelta(days=random.randint(0, 180))
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
        record_date = today - timedelta(days=random.randint(0, 180))
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

