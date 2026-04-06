"""
Financial record routes.

Endpoints for managing financial records with role-based access.
Analysts and admins can read records; only admins can create, update, or delete.

Routes:
    POST   /api/records       — Create a new record (Admin only)
    GET    /api/records       — List records with filtering (Analyst/Admin)
    GET    /api/records/:id   — Get a specific record (Analyst/Admin)
    PUT    /api/records/:id   — Update a record (Admin only)
    DELETE /api/records/:id   — Delete a record (Admin only)
"""

from typing import Tuple, Union

from datetime import date as dt_date

from flask import Blueprint, request, g

from app.middleware.auth import require_auth
from app.middleware.rbac import require_role
from app.extensions import limiter
from app.models.record import RecordType
from app.schemas.record import RecordCreateSchema, RecordUpdateSchema
from app.services import record_service
from app.utils.exceptions import ValidationError
from app.utils.responses import success_response, created_response, no_content_response

record_bp = Blueprint("records", __name__, url_prefix="/api/records")

# Schema instances (reusable, thread-safe for loading)
_create_schema = RecordCreateSchema()
_update_schema = RecordUpdateSchema()

# Constants for validation
VALID_RECORD_TYPES = tuple(record_type.value for record_type in RecordType)
VALID_SORT_FIELDS = ("date", "amount", "category", "type", "created_at")
VALID_SORT_ORDERS = ("asc", "desc")


@record_bp.route("", methods=["POST"])
@require_auth
@require_role("admin")
@limiter.limit("60 per hour")
def create_record() -> Tuple[dict, int]:
    """
    Create a new financial record.

    Requires: Admin role.

    Request Body:
        {
            "amount": 5000.00,          (required, positive number)
            "type": "income",            (required, 'income' or 'expense')
            "category": "Salary",        (required, 1-100 chars)
            "date": "2025-03-15",        (required, YYYY-MM-DD, not in future)
            "description": "March pay"   (optional, max 500 chars)
        }

    Returns:
        201: Created record data
        400: Validation errors
        403: Insufficient permissions

    ---
    tags:
      - Records
    summary: Create financial record
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [amount, type, category, date]
          properties:
            amount: {type: number, format: float, example: 5000.0}
            type: {type: string, enum: [income, expense]}
            category: {type: string, example: Salary}
            date: {type: string, format: date, example: "2025-03-15"}
            description: {type: string, example: March pay}
    responses:
      201:
        description: Record created
      400:
        description: Validation error
      403:
        description: Admin role required
    """
    data = _create_schema.load(request.get_json(force=True))
    record = record_service.create_record(data, created_by_user_id=g.current_user.id)
    return created_response(data=record, message="Financial record created successfully")


@record_bp.route("", methods=["GET"])
@require_auth
@require_role("analyst", "admin")
def list_records() -> Tuple[dict, int]:
    """
    List financial records with optional filtering, sorting, and pagination.

    Requires: Any authenticated role.

    Query Parameters (all optional):
        type        — Filter by 'income' or 'expense'
        category    — Filter by category (case-insensitive partial match)
        date_from   — Records on or after this date (YYYY-MM-DD)
        date_to     — Records on or before this date (YYYY-MM-DD)
        min_amount  — Records with amount >= this value
        max_amount  — Records with amount <= this value
        sort_by     — Sort field: 'date', 'amount', 'category', 'type', 'created_at'
        sort_order  — Sort direction: 'asc' or 'desc' (default: 'desc')
        page        — Page number (default: 1)
        per_page    — Records per page (default: 20, max: 100)

    Returns:
        200: Paginated list of records with pagination metadata

    ---
    tags:
      - Records
    summary: List financial records
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: type
        type: string
        enum: [income, expense]
      - in: query
        name: category
        type: string
      - in: query
        name: date_from
        type: string
        format: date
      - in: query
        name: date_to
        type: string
        format: date
      - in: query
        name: min_amount
        type: number
      - in: query
        name: max_amount
        type: number
      - in: query
        name: sort_by
        type: string
        enum: [date, amount, category, type, created_at]
      - in: query
        name: sort_order
        type: string
        enum: [asc, desc]
      - in: query
        name: page
        type: integer
      - in: query
        name: per_page
        type: integer
    responses:
      200:
        description: Records retrieved
    """
    filters = {}

    # Type filter (validated against allowed values)
    record_type = request.args.get("type")
    if record_type:
        if record_type not in VALID_RECORD_TYPES:
            raise ValidationError(
                "Invalid type filter. Must be 'income' or 'expense'."
            )
        filters["type"] = record_type

    # Category filter
    if request.args.get("category"):
        filters["category"] = request.args.get("category")

    # Date range filters (parsed and validated)
    if request.args.get("date_from"):
        try:
            filters["date_from"] = dt_date.fromisoformat(request.args.get("date_from"))
        except ValueError:
            raise ValidationError("date_from must be in YYYY-MM-DD format")
    if request.args.get("date_to"):
        try:
            filters["date_to"] = dt_date.fromisoformat(request.args.get("date_to"))
        except ValueError:
            raise ValidationError("date_to must be in YYYY-MM-DD format")

    # Amount range filters
    if request.args.get("min_amount"):
        try:
            filters["min_amount"] = float(request.args.get("min_amount"))
        except ValueError:
            raise ValidationError("min_amount must be a valid number")
    if request.args.get("max_amount"):
        try:
            filters["max_amount"] = float(request.args.get("max_amount"))
        except ValueError:
            raise ValidationError("max_amount must be a valid number")

    # Sorting
    sort_by = request.args.get("sort_by", "date")
    if sort_by not in VALID_SORT_FIELDS:
        raise ValidationError(
            f"Invalid sort_by value. Must be one of: {', '.join(VALID_SORT_FIELDS)}"
        )
    filters["sort_by"] = sort_by

    sort_order = request.args.get("sort_order", "desc")
    if sort_order not in VALID_SORT_ORDERS:
        raise ValidationError("sort_order must be 'asc' or 'desc'")
    filters["sort_order"] = sort_order

    # Pagination
    filters["page"] = request.args.get("page", 1)
    filters["per_page"] = request.args.get("per_page", 20)

    result = record_service.list_records(filters)
    return success_response(
        data=result,
        message=f"Retrieved {len(result['records'])} records",
    )


@record_bp.route("/<record_id>", methods=["GET"])
@require_auth
@require_role("analyst", "admin")
def get_record(record_id: str) -> Tuple[dict, int]:
    """
    Get a specific financial record by ID.

    Requires: Any authenticated role.

    Path Parameters:
        record_id: UUID of the record

    Returns:
        200: Record data
        404: Record not found

    ---
    tags:
      - Records
    summary: Get record by ID
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: record_id
        required: true
        type: string
    responses:
      200:
        description: Record retrieved
      404:
        description: Record not found
    """
    record = record_service.get_record_by_id(record_id)
    return success_response(data=record)


@record_bp.route("/<record_id>", methods=["PUT"])
@require_auth
@require_role("admin")
@limiter.limit("120 per hour")
def update_record(record_id: str) -> Tuple[dict, int]:
    """
    Update a financial record.

    Requires: Admin role.

    Path Parameters:
        record_id: UUID of the record

    Request Body (all fields optional):
        {
            "amount": 6000.00,
            "type": "income",
            "category": "Bonus",
            "date": "2025-03-20",
            "description": "Quarterly bonus"
        }

    Returns:
        200: Updated record data
        400: Validation errors
        403: Insufficient permissions
        404: Record not found

    ---
    tags:
      - Records
    summary: Update record
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: record_id
        required: true
        type: string
      - in: body
        name: body
        schema:
          type: object
          properties:
            amount: {type: number}
            type: {type: string, enum: [income, expense]}
            category: {type: string}
            date: {type: string, format: date}
            description: {type: string}
    responses:
      200:
        description: Record updated
      400:
        description: Validation error
      403:
        description: Admin role required
      404:
        description: Record not found
    """
    data = _update_schema.load(request.get_json(force=True))
    if not data:
        raise ValidationError("No valid fields provided for update")

    record = record_service.update_record(record_id, data)
    return success_response(data=record, message="Financial record updated successfully")


@record_bp.route("/<record_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
@limiter.limit("60 per hour")
def delete_record(record_id: str) -> Union[Tuple[str, int], Tuple[dict, int]]:
    """
    Delete a financial record.

    Requires: Admin role.

    Path Parameters:
        record_id: UUID of the record

    Returns:
        204: No content (successfully deleted)
        403: Insufficient permissions
        404: Record not found

    ---
    tags:
      - Records
    summary: Soft-delete record
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: record_id
        required: true
        type: string
    responses:
      204:
        description: Record deleted
      403:
        description: Admin role required
      404:
        description: Record not found
    """
    record_service.delete_record(record_id)
    return no_content_response()
