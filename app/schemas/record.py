"""
Financial record validation schemas.

Defines Marshmallow schemas for validating financial record input.
Includes business rule validation such as ensuring amounts are positive
and dates are not in the future.
"""

from datetime import date as dt_date
from typing import Optional

from marshmallow import Schema, fields, validate, validates, ValidationError

from app.models.record import FinancialRecord, RecordType


class RecordCreateSchema(Schema):
    """
    Validates financial record creation input.

    Required fields: amount, type, category, date.
    Optional fields: description.
    """

    amount = fields.Float(
        required=True,
        error_messages={"required": "Amount is required", "invalid": "Amount must be a number"},
    )
    type = fields.String(
        required=True,
        validate=validate.OneOf([e.value for e in RecordType]),
        error_messages={
            "required": "Type is required",
            "invalid": f"Type must be one of: {', '.join([e.value for e in RecordType])}",
        },
    )
    category = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "Category is required"},
    )
    date = fields.Date(
        required=True,
        error_messages={
            "required": "Date is required",
            "invalid": "Date must be in YYYY-MM-DD format",
        },
    )
    description = fields.String(
        load_default=None,
        validate=validate.Length(max=500),
    )

    @validates("amount")
    def validate_amount_positive(self, value: float) -> None:
        """Ensure amount is a positive number."""
        if value <= 0:
            raise ValidationError("Amount must be greater than zero")
        # Limit to 2 decimal places for currency
        if round(value, 2) != value:
            raise ValidationError("Amount can have at most 2 decimal places")

    @validates("date")
    def validate_date_not_future(self, value: dt_date) -> None:
        """Ensure the transaction date is not in the future."""
        if value > dt_date.today():
            raise ValidationError("Date cannot be in the future")

    @validates("category")
    def validate_category_not_blank(self, value: str) -> None:
        """Ensure category is not just whitespace."""
        if not value.strip():
            raise ValidationError("Category cannot be blank")


class RecordUpdateSchema(Schema):
    """
    Validates financial record update input.

    All fields are optional — only provided fields are updated.
    Same validation rules apply as creation.
    """

    amount = fields.Float(
        error_messages={"invalid": "Amount must be a number"},
    )
    type = fields.String(
        validate=validate.OneOf([e.value for e in RecordType]),
    )
    category = fields.String(
        validate=validate.Length(min=1, max=100),
    )
    date = fields.Date(
        error_messages={"invalid": "Date must be in YYYY-MM-DD format"},
    )
    description = fields.String(
        validate=validate.Length(max=500),
        allow_none=True,
    )

    @validates("amount")
    def validate_amount_positive(self, value: Optional[float]) -> None:
        if value is not None and value <= 0:
            raise ValidationError("Amount must be greater than zero")
        if value is not None and round(value, 2) != value:
            raise ValidationError("Amount can have at most 2 decimal places")

    @validates("date")
    def validate_date_not_future(self, value: Optional[dt_date]) -> None:
        if value is not None and value > dt_date.today():
            raise ValidationError("Date cannot be in the future")

    @validates("category")
    def validate_category_not_blank(self, value: Optional[str]) -> None:
        if value is not None and not value.strip():
            raise ValidationError("Category cannot be blank")
