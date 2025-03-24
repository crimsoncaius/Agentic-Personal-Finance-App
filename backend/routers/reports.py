# app/routers/reports.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import models
from ..schemas import TransactionType

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/summary")
def get_finance_summary(db: Session = Depends(get_db)):
    """
    Returns a simple summary:
    - total_expenses
    - total_incomes
    - net (incomes - expenses)
    """
    expenses = db.query(models.Transaction).filter(models.Transaction.transaction_type == TransactionType.EXPENSE).all()
    incomes = db.query(models.Transaction).filter(models.Transaction.transaction_type == TransactionType.INCOME).all()

    sum_expenses = sum(t.amount for t in expenses)
    sum_incomes = sum(t.amount for t in incomes)
    
    return {
        "total_expenses": sum_expenses,
        "total_incomes": sum_incomes,
        "net": sum_incomes - sum_expenses
    } 