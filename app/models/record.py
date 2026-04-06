"""
Financial record model definition.

Represents a single financial entry (income or expense) in the system.
Each record is linked to the user who created it via a foreign key,
providing a complete audit trail.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Dict, Any

from app.extensions import db


class RecordType(str, PyEnum):
    INCOME = "income"
    EXPENSE = "expense"


class FinancialRecord(db.Model):
    """
    Financial record model.

    Attributes:
        id: UUID primary key.
        amount: Monetary value of the transaction (always positive).
        type: Classification — 'income' or 'expense'.
        category: Descriptive category (e.g., 'Salary', 'Rent', 'Utilities').
        date: The date the transaction occurred.
        description: Optional free-text notes about the transaction.
        created_by: Foreign key linking to the user who created this record.
        created_at: Timestamp of record creation (UTC).
        updated_at: Timestamp of last update (UTC, auto-updated).
    """

    __tablename__ = "financial_records"
    __table_args__ = (
        db.UniqueConstraint(
            'amount', 'type', 'category', 'date', 'created_by',
            name='uix_financial_record_duplicate'
        ),
    )

    # Predefined categories for consistency (not strictly enforced — users
    # can provide custom categories, but these serve as suggestions)
    SUGGESTED_CATEGORIES = (
        "Salary",
        "Freelance",
        "Investment",
        "Rent",
        "Utilities",
        "Groceries",
        "Transport",
        "Healthcare",
        "Entertainment",
        "Education",
        "Shopping",
        "Travel",
        "Insurance",
        "Taxes",
        "Other",
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    type = db.Column(db.Enum(RecordType), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(500), nullable=True)
    created_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to a dictionary for API responses."""
        return {
            "id": self.id,
            "amount": float(self.amount),
            "type": self.type.value,
            "category": self.category,
            "date": self.date.isoformat(),
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }

    def __repr__(self) -> str:
        return f"<FinancialRecord {self.type}: {self.amount} ({self.category})>"
