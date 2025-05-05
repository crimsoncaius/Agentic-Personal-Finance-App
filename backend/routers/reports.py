# app/routers/reports.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from .. import models
from ..schemas import TransactionType
from ..auth import get_current_active_user
from ..models import User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def get_finance_summary(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Returns a simple summary:
    - total_expenses
    - total_incomes
    - net (incomes - expenses)
    """
    expenses = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.transaction_type == TransactionType.EXPENSE,
            models.Transaction.user_id == current_user.id,
        )
        .all()
    )
    incomes = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.transaction_type == TransactionType.INCOME,
            models.Transaction.user_id == current_user.id,
        )
        .all()
    )

    sum_expenses = sum(t.amount for t in expenses)
    sum_incomes = sum(t.amount for t in incomes)

    return {
        "total_expenses": sum_expenses,
        "total_incomes": sum_incomes,
        "net": sum_incomes - sum_expenses,
    }


@router.get("/breakdown")
def get_expense_breakdown(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Returns a detailed breakdown of all expenses with their categories
    """
    try:
        # Query transactions with their categories
        expenses = (
            db.query(
                models.Transaction.id,
                models.Transaction.amount,
                models.Transaction.date,
                models.Transaction.description,
                models.Category.name.label("category"),
                models.Transaction.transaction_type,
            )
            .outerjoin(models.Category)
            .filter(
                models.Transaction.transaction_type == TransactionType.EXPENSE,
                models.Transaction.user_id == current_user.id,
            )
            .order_by(models.Transaction.date.desc(), models.Transaction.id.desc())
            .all()
        )

        # Format the results
        return [
            {
                "date": expense.date.isoformat(),
                "description": expense.description,
                "category": expense.category or "Uncategorized",
                "amount": expense.amount,
            }
            for expense in expenses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-category")
def get_totals_by_category(
    transaction_type: TransactionType = TransactionType.EXPENSE,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns total amount grouped by category for the given transaction_type and date range.
    """
    try:
        # Build base query for transactions
        transaction_query = db.query(models.Transaction).filter(
            models.Transaction.transaction_type == transaction_type,
            models.Transaction.user_id == current_user.id,
        )
        if start_date and end_date:
            transaction_query = transaction_query.filter(
                models.Transaction.date >= start_date,
                models.Transaction.date <= end_date,
            )

        # Query totals by category
        category_totals = (
            db.query(
                models.Category.name.label("category"),
                func.sum(models.Transaction.amount).label("total"),
            )
            .outerjoin(
                models.Transaction,
                (models.Transaction.category_id == models.Category.id)
                & (models.Transaction.user_id == current_user.id),
            )
            .filter(models.Category.user_id == current_user.id)
            .filter(models.Category.transaction_type == transaction_type)
        )
        if start_date and end_date:
            category_totals = category_totals.filter(
                models.Transaction.date >= start_date,
                models.Transaction.date <= end_date,
            )
        category_totals = (
            category_totals.group_by(models.Category.name)
            .order_by(func.sum(models.Transaction.amount).desc())
            .all()
        )

        # Handle uncategorized totals
        uncategorized_query = db.query(
            func.sum(models.Transaction.amount).label("total")
        ).filter(
            models.Transaction.category_id.is_(None),
            models.Transaction.transaction_type == transaction_type,
            models.Transaction.user_id == current_user.id,
        )
        if start_date and end_date:
            uncategorized_query = uncategorized_query.filter(
                models.Transaction.date >= start_date,
                models.Transaction.date <= end_date,
            )
        uncategorized = uncategorized_query.scalar()

        # Format the results
        results = [
            {
                "category": total.category or "Uncategorized",
                "total": float(total.total) if total.total else 0.0,
            }
            for total in category_totals
        ]
        if uncategorized:
            results.append({"category": "Uncategorized", "total": float(uncategorized)})
        return sorted(results, key=lambda x: x["total"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
