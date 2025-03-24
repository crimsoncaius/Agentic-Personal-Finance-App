# app/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from enum import Enum

# Enums
class TransactionType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class RecurrencePeriod(str, Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"

# Category Schemas
class CategoryCreate(BaseModel):
    name: str = Field(..., example="Food")
    transaction_type: TransactionType = Field(..., example="EXPENSE")

class CategoryRead(BaseModel):
    id: int
    name: str
    transaction_type: TransactionType

    model_config = {"from_attributes": True}

# Transaction Schemas
class TransactionBase(BaseModel):
    amount: float = Field(..., example=50.75)
    date: Optional[datetime.date] = Field(None, example="2025-03-20")
    description: Optional[str] = Field(None, example="Grocery shopping")
    is_recurring: bool = Field(False)
    recurrence_period: RecurrencePeriod = Field(default=RecurrencePeriod.NONE)
    transaction_type: TransactionType = Field(..., example="EXPENSE")
    category_id: int = Field(..., example=1)

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    pass

class TransactionRead(TransactionBase):
    id: int

    model_config = {"from_attributes": True} 