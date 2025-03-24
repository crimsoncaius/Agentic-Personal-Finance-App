# app/init_db.py

from .database import SessionLocal
from .models import Category
from .schemas import TransactionType

def seed_categories():
    db = SessionLocal()
    
    # Clear existing categories
    try:
        db.query(Category).delete()
        db.commit()
    except:
        db.rollback()
    
    predefined_categories = [
        # Expense categories
        {"name": "Transportation", "type": TransactionType.EXPENSE},
        {"name": "Food & Groceries", "type": TransactionType.EXPENSE},
        {"name": "Utilities", "type": TransactionType.EXPENSE},
        {"name": "Healthcare", "type": TransactionType.EXPENSE},
        {"name": "Entertainment", "type": TransactionType.EXPENSE},
        {"name": "Shopping", "type": TransactionType.EXPENSE},
        {"name": "Personal Care", "type": TransactionType.EXPENSE},
        {"name": "Education", "type": TransactionType.EXPENSE},
        {"name": "Misc", "type": TransactionType.EXPENSE},
        # Income category
        {"name": "Income", "type": TransactionType.INCOME}
    ]
    
    for category in predefined_categories:
        existing = db.query(Category).filter(Category.name == category["name"]).first()
        if not existing:
            new_cat = Category(name=category["name"], transaction_type=category["type"])
            db.add(new_cat)
    db.commit()
    db.close() 