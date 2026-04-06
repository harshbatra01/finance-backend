"""
Financial record service module.

Contains all business logic for managing financial records, including CRUD
operations and advanced filtering. Keeps route handlers thin by encapsulating
data access patterns and query building here.

Design Decisions:
    - Filtering uses dynamic query building — only filters that are provided
      in the request are applied, allowing flexible queries.
    - Records are always associated with the user who created them via
      the `created_by` field for audit purposes.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.record import FinancialRecord, RecordType
from app.utils.exceptions import NotFoundError, ConflictError

# Whitelist of fields that can be used for sorting (prevents injection)
SORTABLE_FIELDS = {
    "date": FinancialRecord.date,
    "amount": FinancialRecord.amount,
    "category": FinancialRecord.category,
    "type": FinancialRecord.type,
    "created_at": FinancialRecord.created_at,
}


def create_record(data: Dict[str, Any], created_by_user_id: str) -> Dict[str, Any]:
    """
    Create a new financial record.

    Args:
        data: Dict with keys: amount, type, category, date, and optionally description.
        created_by_user_id: UUID of the user creating the record (from auth context).

    Returns:
        dict: The created record's serialized data.
    """
    record = FinancialRecord(
        amount=data["amount"],
        type=RecordType(data["type"]),
        category=data["category"],
        date=data["date"],
        description=data.get("description"),
        created_by=created_by_user_id,
    )

    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(
            "Duplicate financial record detected for this user on the same date."
        ) from exc

    return record.to_dict()


def get_record_by_id(record_id: str) -> Dict[str, Any]:
    """
    Retrieve a single financial record by ID.

    Args:
        record_id: UUID string of the record.

    Returns:
        dict: The record's serialized data.

    Raises:
        NotFoundError: If no record exists with the given ID.
    """
    record = db.session.get(FinancialRecord, record_id)
    if not record or record.deleted_at is not None:
        raise NotFoundError(f"Financial record with ID '{record_id}' not found")
    return record.to_dict()


def list_records(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    List financial records with optional filtering and sorting.

    Supports the following filters (all optional):
        - type: Filter by 'income' or 'expense'
        - category: Filter by category name (case-insensitive partial match)
        - date_from: Only records on or after this date
        - date_to: Only records on or before this date
        - min_amount: Only records with amount >= this value
        - max_amount: Only records with amount <= this value
        - created_by: Only records created by a specific user
        - sort_by: Field to sort by (default: 'date')
        - sort_order: 'asc' or 'desc' (default: 'desc')
        - page: Page number for pagination (default: 1)
        - per_page: Records per page (default: 20, max: 100)

    Args:
        filters: Optional dict of filter parameters.

    Returns:
        dict: Contains 'records' (list of dicts) and 'pagination' metadata.
    """
    query = FinancialRecord.query.filter(FinancialRecord.deleted_at.is_(None))
    filters = filters or {}

    # --- Apply filters ---
    if filters.get("type"):
        query = query.filter(FinancialRecord.type == RecordType(filters["type"]))

    if filters.get("category"):
        # Case-insensitive partial match for better UX
        query = query.filter(
            FinancialRecord.category.ilike(f"%{filters['category']}%")
        )

    if filters.get("date_from"):
        query = query.filter(FinancialRecord.date >= filters["date_from"])

    if filters.get("date_to"):
        query = query.filter(FinancialRecord.date <= filters["date_to"])

    if filters.get("min_amount"):
        query = query.filter(FinancialRecord.amount >= filters["min_amount"])

    if filters.get("max_amount"):
        query = query.filter(FinancialRecord.amount <= filters["max_amount"])

    if filters.get("created_by"):
        query = query.filter(FinancialRecord.created_by == filters["created_by"])

    # --- Sorting ---
    sort_field = filters.get("sort_by", "date")
    sort_order = filters.get("sort_order", "desc")

    sort_column = SORTABLE_FIELDS.get(sort_field, FinancialRecord.date)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # --- Pagination ---
    page = max(1, int(filters.get("page", 1)))
    per_page = min(100, max(1, int(filters.get("per_page", 20))))

    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)

    records = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "records": [record.to_dict() for record in records],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    }


def update_record(record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing financial record.

    Only updates fields that are present in the data dict, leaving
    other fields unchanged.

    Args:
        record_id: UUID string of the record.
        data: Dict with optional keys: amount, type, category, date, description.

    Returns:
        dict: The updated record's serialized data.

    Raises:
        NotFoundError: If no record exists with the given ID.
    """
    record = db.session.get(FinancialRecord, record_id)
    if not record or record.deleted_at is not None:
        raise NotFoundError(f"Financial record with ID '{record_id}' not found")

    # Update only provided fields
    if "amount" in data:
        record.amount = data["amount"]
    if "type" in data:
        record.type = RecordType(data["type"])
    if "category" in data:
        record.category = data["category"]
    if "date" in data:
        record.date = data["date"]
    if "description" in data:
        record.description = data["description"]

    record.updated_at = datetime.now(timezone.utc)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(
            "Update would create a duplicate financial record."
        ) from exc

    return record.to_dict()


def delete_record(record_id: str) -> None:
    """
    Permanently delete a financial record.

    Args:
        record_id: UUID string of the record.

    Raises:
        NotFoundError: If no record exists with the given ID.
    """
    record = db.session.get(FinancialRecord, record_id)
    if not record or record.deleted_at is not None:
        raise NotFoundError(f"Financial record with ID '{record_id}' not found")

    record.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
