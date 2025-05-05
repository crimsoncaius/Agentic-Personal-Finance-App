# app/schemas.py

from pydantic import BaseModel, Field, validator, constr
from typing import Optional, List, TypeVar, Generic
import datetime
from enum import Enum


# Enums
class TransactionType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


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
    amount: float = Field(
        ...,
        example=50.75,
        gt=0,
        description="Transaction amount must be greater than 0",
    )
    date: Optional[datetime.date] = Field(
        None,
        example="2025-03-20",
        description="Transaction date (defaults to current date if not provided)",
    )
    description: constr(min_length=1, max_length=500) = Field(
        ...,
        example="Grocery shopping",
        description="Description of the transaction (1-500 characters required)",
    )
    transaction_type: TransactionType = Field(
        ..., example="EXPENSE", description="Type of transaction (INCOME or EXPENSE)"
    )
    category_id: int = Field(
        ..., example=1, gt=0, description="ID of the associated category"
    )

    @validator("date")
    def validate_date(cls, v):
        if v and v > datetime.date.today():
            raise ValueError("Transaction date cannot be in the future")
        return v

    @validator("amount")
    def validate_amount(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Amount must be a number")
        if v > 1000000000:  # 1 billion limit
            raise ValueError("Amount cannot exceed 1 billion")
        return round(v, 2)  # Round to 2 decimal places


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
