"""
Dashboard summary routes.

Endpoints for retrieving aggregated financial data for dashboard display.
Accessible to all roles — viewers have dashboard-only access in this system.

Routes:
    GET /api/dashboard/summary            — Overall financial summary
    GET /api/dashboard/category-breakdown — Category-wise breakdown
    GET /api/dashboard/trends             — Monthly trends (last 12 months)
    GET /api/dashboard/recent-activity    — Most recent records
"""

from typing import Tuple

from flask import Blueprint, request

from app.middleware.auth import require_auth
from app.middleware.rbac import require_role
from app.services import dashboard_service
from app.utils.responses import success_response

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/summary", methods=["GET"])
@require_auth
@require_role("viewer", "analyst", "admin")
def get_summary() -> Tuple[dict, int]:
    """
    Get overall financial summary.

    Requires: Any authenticated role.

    Returns:
        200: Summary containing total_income, total_expenses,
             net_balance, and total_records.

    Example Response:
        {
            "success": true,
            "data": {
                "total_income": 85000.00,
                "total_expenses": 42500.00,
                "net_balance": 42500.00,
                "total_records": 30
            }
        }

    ---
    tags:
      - Dashboard
    summary: Get financial summary
    security:
      - bearerAuth: []
    responses:
      200:
        description: Summary retrieved
      403:
        description: Analyst/admin role required
    """
    summary = dashboard_service.get_summary()
    return success_response(data=summary, message="Dashboard summary retrieved")


@dashboard_bp.route("/category-breakdown", methods=["GET"])
@require_auth
@require_role("viewer", "analyst", "admin")
def get_category_breakdown() -> Tuple[dict, int]:
    """
    Get income and expense totals grouped by category.

    Requires: Any authenticated role.

    Returns:
        200: List of categories with income, expenses, net amount,
             and record count for each.

    Example Response:
        {
            "success": true,
            "data": [
                {
                    "category": "Salary",
                    "total_income": 60000.00,
                    "total_expenses": 0.00,
                    "net_amount": 60000.00,
                    "record_count": 6
                }
            ]
        }

    ---
    tags:
      - Dashboard
    summary: Get category breakdown
    security:
      - bearerAuth: []
    responses:
      200:
        description: Breakdown retrieved
      403:
        description: Analyst/admin role required
    """
    breakdown = dashboard_service.get_category_breakdown()
    return success_response(
        data=breakdown,
        message=f"Category breakdown retrieved ({len(breakdown)} categories)",
    )


@dashboard_bp.route("/trends", methods=["GET"])
@require_auth
@require_role("viewer", "analyst", "admin")
def get_trends() -> Tuple[dict, int]:
    """
    Get monthly income and expense trends.

    Requires: Any authenticated role.

    Query Parameters:
        months (optional): Number of months to include (default: 12, max: 24)

    Returns:
        200: List of monthly data points with income, expenses, and net.
             Months with no records are included with zero values for
             continuous chart rendering.

    ---
    tags:
      - Dashboard
    summary: Get monthly financial trends
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: months
        type: integer
        default: 12
    responses:
      200:
        description: Trends retrieved
      403:
        description: Analyst/admin role required
    """
    months = request.args.get("months", 12, type=int)
    months = min(24, max(1, months))  # Clamp to valid range

    trends = dashboard_service.get_monthly_trends(months=months)
    return success_response(
        data=trends,
        message=f"Monthly trends retrieved ({len(trends)} months)",
    )


@dashboard_bp.route("/recent-activity", methods=["GET"])
@require_auth
@require_role("viewer", "analyst", "admin")
def get_recent_activity() -> Tuple[dict, int]:
    """
    Get the most recent financial records.

    Requires: Any authenticated role.

    Query Parameters:
        limit (optional): Number of records to return (default: 10, max: 50)

    Returns:
        200: List of recent records, newest first.

    ---
    tags:
      - Dashboard
    summary: Get recent financial activity
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: limit
        type: integer
        default: 10
    responses:
      200:
        description: Recent activity retrieved
      403:
        description: Analyst/admin role required
    """
    limit = request.args.get("limit", 10, type=int)
    limit = min(50, max(1, limit))  # Clamp to valid range

    records = dashboard_service.get_recent_activity(limit=limit)
    return success_response(
        data=records,
        message=f"Retrieved {len(records)} recent records",
    )
