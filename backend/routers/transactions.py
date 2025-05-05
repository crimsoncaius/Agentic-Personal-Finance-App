# app/routers/transactions.py

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import desc, asc, and_
from datetime import date
from math import ceil
import logging

from ..database import get_db
from .. import models
from ..schemas import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
    PaginatedResponse,
)
from ..auth import get_current_active_user
from ..models import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionRead)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        # Validate category belongs to user and matches transaction type
        category = (
            db.query(models.Category)
            .filter(
                models.Category.id == transaction.category_id,
                models.Category.user_id == current_user.id,
            )
            .first()
        )
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category ID")

        # Validate category type matches transaction type
        if category.transaction_type != transaction.transaction_type:
            raise HTTPException(
                status_code=400,
                detail=f"Category type ({category.transaction_type}) does not match transaction type ({transaction.transaction_type})",
            )

        db_transaction = models.Transaction(
            amount=transaction.amount,
            date=transaction.date or date.today(),
            description=transaction.description,
            transaction_type=transaction.transaction_type,
            category_id=transaction.category_id,
            user_id=current_user.id,
        )
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        logger.info(
            f"Created transaction {db_transaction.id} for user {current_user.id}"
        )
        return db_transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating transaction")


@router.get("", response_model=PaginatedResponse[TransactionRead])
async def list_transactions(
    page: int = 0,
    page_size: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_desc: bool = False,
    filter_date: Optional[str] = None,
    filter_description: Optional[str] = None,
    filter_category_id: Optional[int] = None,
    filter_amount: Optional[float] = None,
    filter_transaction_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )

    # Apply date filters if both dates are provided
    if start_date and end_date:
        query = query.filter(
            models.Transaction.date >= start_date, models.Transaction.date <= end_date
        )

    # Apply column filters
    if filter_date:
        query = query.filter(models.Transaction.date == filter_date)
    if filter_description:
        query = query.filter(
            models.Transaction.description.ilike(f"%{filter_description}%")
        )
    if filter_category_id:
        query = query.filter(models.Transaction.category_id == filter_category_id)
    if filter_amount:
        query = query.filter(models.Transaction.amount == filter_amount)
    if filter_transaction_type:
        query = query.filter(
            models.Transaction.transaction_type == filter_transaction_type
        )

    # Apply sorting
    if sort_by:
        # Get the column to sort by
        sort_column = getattr(models.Transaction, sort_by, None)
        if sort_column is not None:
            if sort_by == "date":
                # Sort by date, then by id (both descending if sort_desc)
                if sort_desc:
                    query = query.order_by(
                        sort_column.desc(), models.Transaction.id.desc()
                    )
                else:
                    query = query.order_by(
                        sort_column.asc(), models.Transaction.id.asc()
                    )
            else:
                query = query.order_by(
                    sort_column.desc() if sort_desc else sort_column.asc()
                )
    else:
        # Default sort by date descending, then id descending
        query = query.order_by(
            models.Transaction.date.desc(), models.Transaction.id.desc()
        )

    # Get total count for pagination
    total = query.count()

    # Apply pagination
    query = query.offset(page * page_size).limit(page_size)

    # Execute query
    transactions = query.all()

    return {
        "data": transactions,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        # Verify transaction exists and belongs to user
        db_transaction = (
            db.query(models.Transaction)
            .filter(
                models.Transaction.id == transaction_id,
                models.Transaction.user_id == current_user.id,
            )
            .first()
        )
        if not db_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Validate category belongs to user and matches transaction type
        category = (
            db.query(models.Category)
            .filter(
                models.Category.id == transaction.category_id,
                models.Category.user_id == current_user.id,
            )
            .first()
        )
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category ID")

        # Validate category type matches transaction type
        if category.transaction_type != transaction.transaction_type:
            raise HTTPException(
                status_code=400,
                detail=f"Category type ({category.transaction_type}) does not match transaction type ({transaction.transaction_type})",
            )

        # Update transaction fields
        for key, value in transaction.dict(exclude_unset=True).items():
            setattr(db_transaction, key, value)

        db.commit()
        db.refresh(db_transaction)
        logger.info(f"Updated transaction {transaction_id} for user {current_user.id}")
        return db_transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating transaction")


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(db_transaction)
    db.commit()
    return {"detail": "Transaction deleted successfully"}
