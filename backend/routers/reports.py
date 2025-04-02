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
def get_expenses_by_category(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Returns total expenses grouped by category
    """
    try:
        # Query total expenses by category
        category_totals = (
            db.query(
                models.Category.name.label("category"),
                func.sum(models.Transaction.amount).label("total"),
            )
            .outerjoin(models.Transaction)
            .filter(
                models.Transaction.transaction_type == TransactionType.EXPENSE,
                models.Transaction.user_id == current_user.id,
            )
            .group_by(models.Category.name)
            .order_by(func.sum(models.Transaction.amount).desc())
            .all()
        )

        # Handle uncategorized expenses
        uncategorized = (
            db.query(func.sum(models.Transaction.amount).label("total"))
            .filter(
                models.Transaction.category_id.is_(None),
                models.Transaction.transaction_type == TransactionType.EXPENSE,
                models.Transaction.user_id == current_user.id,
            )
            .scalar()
        )

        # Format the results
        results = [
            {"category": total.category or "Uncategorized", "total": float(total.total)}
            for total in category_totals
        ]

        # Add uncategorized total if exists
        if uncategorized:
            results.append({"category": "Uncategorized", "total": float(uncategorized)})

        return sorted(results, key=lambda x: x["total"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
