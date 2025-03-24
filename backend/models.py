# app/models.py

from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SAEnum
from datetime import date

from .database import Base
from .schemas import TransactionType, RecurrencePeriod

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    transaction_type = Column(SAEnum(TransactionType), nullable=False)

    transactions = relationship("Transaction", back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, default=func.current_date())
    description = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_period = Column(SAEnum(RecurrencePeriod), default=RecurrencePeriod.NONE)
    transaction_type = Column(SAEnum(TransactionType), nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="transactions") 