"""
Dashboard service module.

Contains business logic for computing aggregated financial data suitable
for dashboard display. All analytics are computed via SQL-level aggregations
for efficiency rather than loading all records into memory.

Design Decisions:
    - Aggregations use SQLAlchemy's func module for database-level computation,
      which is far more efficient than Python-level aggregation.
    - Monthly trends use a rolling 12-month window for relevance.
    - All monetary values are rounded to 2 decimal places for consistency.
"""

from datetime import date, timedelta
from typing import Dict, Any, List

from sqlalchemy import func, case, extract

from app.extensions import db
from app.models.record import FinancialRecord, RecordType

# Month name lookup for trend labels
MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def get_summary() -> Dict[str, Any]:
    """
    Compute overall financial summary.

    Returns a snapshot of:
        - total_income: Sum of all income records
        - total_expenses: Sum of all expense records
        - net_balance: Income minus expenses
        - total_records: Count of all records

    Returns:
        dict: Financial summary with the above fields.
    """
    result = db.session.query(
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                    else_=0
                )
            ), 0
        ).label("total_income"),
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                    else_=0
                )
            ), 0
        ).label("total_expenses"),
        func.count(FinancialRecord.id).label("total_records"),
    ).filter(
        FinancialRecord.deleted_at.is_(None)
    ).first()

    total_income = round(float(result.total_income), 2)
    total_expenses = round(float(result.total_expenses), 2)
    net_balance = round(total_income - total_expenses, 2)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": net_balance,
        "total_records": result.total_records,
    }


def get_category_breakdown() -> List[Dict[str, Any]]:
    """
    Compute income and expense totals grouped by category.

    Returns each category with its total income, total expenses, net amount,
    and transaction count — useful for pie charts and category analysis.

    Results are sorted by total amount (descending) for importance ordering.

    Returns:
        list[dict]: Each dict contains category, total_income, total_expenses,
                    net_amount, and record_count.
    """
    results = db.session.query(
        FinancialRecord.category,
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                    else_=0
                )
            ), 0
        ).label("total_income"),
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                    else_=0
                )
            ), 0
        ).label("total_expenses"),
        func.count(FinancialRecord.id).label("record_count"),
    ).filter(
        FinancialRecord.deleted_at.is_(None)
    ).group_by(
        FinancialRecord.category
    ).order_by(
        func.sum(FinancialRecord.amount).desc()
    ).all()

    breakdown = []
    for row in results:
        income = round(float(row.total_income), 2)
        expenses = round(float(row.total_expenses), 2)
        breakdown.append({
            "category": row.category,
            "total_income": income,
            "total_expenses": expenses,
            "net_amount": round(income - expenses, 2),
            "record_count": row.record_count,
        })

    return breakdown


def get_monthly_trends(months: int = 12) -> List[Dict[str, Any]]:
    """
    Compute monthly income and expense trends for the last N months.

    Provides data suitable for line/bar charts showing financial trends
    over time. Months with no records are filled with zero values for
    continuous chart data.

    Args:
        months: Number of months to include (default: 12).

    Returns:
        list[dict]: Each dict contains year, month, month_label,
                    total_income, total_expenses, and net_amount.
                    Sorted chronologically (oldest first).
    """
    # Calculate the start date for the trend window
    today = date.today()
    start_date = today.replace(day=1) - timedelta(days=(months - 1) * 30)
    start_date = start_date.replace(day=1)  # First day of that month

    # Query monthly aggregations from the database
    results = db.session.query(
        extract("year", FinancialRecord.date).label("year"),
        extract("month", FinancialRecord.date).label("month"),
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                    else_=0
                )
            ), 0
        ).label("total_income"),
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                    else_=0
                )
            ), 0
        ).label("total_expenses"),
    ).filter(
        FinancialRecord.date >= start_date,
        FinancialRecord.deleted_at.is_(None)
    ).group_by(
        extract("year", FinancialRecord.date),
        extract("month", FinancialRecord.date),
    ).order_by(
        extract("year", FinancialRecord.date),
        extract("month", FinancialRecord.date),
    ).all()

    # Build a lookup dict from query results
    data_map = {}
    for row in results:
        key = (int(row.year), int(row.month))
        data_map[key] = {
            "total_income": round(float(row.total_income), 2),
            "total_expenses": round(float(row.total_expenses), 2),
        }

    # Generate all months in the range (fill gaps with zeros)
    trends = []
    current = start_date
    while current <= today:
        key = (current.year, current.month)
        month_data = data_map.get(key, {"total_income": 0.0, "total_expenses": 0.0})

        income = month_data["total_income"]
        expenses = month_data["total_expenses"]

        trends.append({
            "year": current.year,
            "month": current.month,
            "month_label": f"{MONTH_NAMES[current.month]} {current.year}",
            "total_income": income,
            "total_expenses": expenses,
            "net_amount": round(income - expenses, 2),
        })

        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return trends


def get_recent_activity(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve the most recent financial records.

    Useful for activity feeds and "recent transactions" dashboard widgets.

    Args:
        limit: Maximum number of records to return (default: 10, max: 50).

    Returns:
        list[dict]: List of recent records, newest first.
    """
    limit = min(50, max(1, limit))

    records = FinancialRecord.query.filter(
        FinancialRecord.deleted_at.is_(None)
    ).order_by(
        FinancialRecord.created_at.desc()
    ).limit(limit).all()

    return [record.to_dict() for record in records]
