from datetime import date, timedelta

import pytest

from app.models.user import User, UserRole
from app.services.record_service import (
    create_record,
    delete_record,
    get_record_by_id,
    list_records,
    update_record,
)
from app.utils.exceptions import NotFoundError


def _admin_user() -> User:
    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    assert admin is not None
    return admin


def test_record_crud_round_trip(app, init_database):
    """Record CRUD returns enum values consistently."""
    with app.app_context():
        admin = _admin_user()
        record = create_record(
            {
                "amount": 1500.25,
                "type": "income",
                "category": "Salary",
                "date": date.today(),
                "description": "Salary credit",
            },
            created_by_user_id=admin.id,
        )
        assert record["type"] == "income"

        updated = update_record(record["id"], {"type": "expense", "amount": 400.75})
        assert updated["type"] == "expense"
        assert updated["amount"] == 400.75


def test_soft_deleted_record_is_hidden_from_reads(app, init_database):
    """Soft-deleted records are excluded from read APIs."""
    with app.app_context():
        admin = _admin_user()
        record = create_record(
            {
                "amount": 220.0,
                "type": "expense",
                "category": "Utilities",
                "date": date.today(),
            },
            created_by_user_id=admin.id,
        )

        delete_record(record["id"])

        with pytest.raises(NotFoundError):
            get_record_by_id(record["id"])

        listed = list_records()
        assert record["id"] not in {item["id"] for item in listed["records"]}


def test_list_records_with_sql_like_category_filter(app, init_database):
    """SQL-like category input should be treated as plain text."""
    with app.app_context():
        admin = _admin_user()
        create_record(
            {
                "amount": 999.99,
                "type": "income",
                "category": "Consulting",
                "date": date.today() - timedelta(days=1),
            },
            created_by_user_id=admin.id,
        )

        result = list_records({"category": "' OR 1=1 --"})
        assert result["records"] == []
