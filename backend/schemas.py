# app/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, TypeVar, Generic
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


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    pageSize: int
    totalPages: int

    model_config = {"from_attributes": True}


# User Schemas
class UserBase(BaseModel):
    email: str = Field(..., example="user@example.com")
    username: str = Field(..., example="johndoe")


class UserCreate(UserBase):
    password: str = Field(..., example="securepassword123")


class UserRead(UserBase):
    id: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., example="securepassword123")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 604800  # 7 days in seconds


class TokenData(BaseModel):
    user_id: int
    email: str


# Chat Schemas
class ChatMessage(BaseModel):
    content: str = Field(..., example="Show me my recent transactions")


class ChatResponse(BaseModel):
    response: str = Field(..., example="Here are your recent transactions...")
    success: bool = Field(..., example=True)
    error: Optional[str] = Field(None, example="Error processing request")
    data: Optional[dict] = Field(None, example={"transactions": []})
