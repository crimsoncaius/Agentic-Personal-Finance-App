# app/init_db.py

from .database import SessionLocal
from .models import Category, User
from .schemas import TransactionType


def seed_categories(user_id: int = None):
    """
    Seed predefined categories for a specific user or all users.
    If user_id is provided, seed only for that user.
    If user_id is None, seed for all users.
    """
    db = SessionLocal()

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
        {"name": "Income", "type": TransactionType.INCOME},
    ]

    try:
        # Get users to seed categories for
        if user_id:
            users = [db.query(User).filter(User.id == user_id).first()]
            if not users[0]:
                raise ValueError(f"User with id {user_id} not found")
        else:
            users = db.query(User).all()

        # Seed categories for each user
        for user in users:
            print(f"Seeding categories for user {user.email}")
            for category in predefined_categories:
                # Check if category exists for this user
                existing = (
                    db.query(Category)
                    .filter(
                        Category.name == category["name"], Category.user_id == user.id
                    )
                    .first()
                )
                if not existing:
                    new_cat = Category(
                        name=category["name"],
                        transaction_type=category["type"],
                        user_id=user.id,
                    )
                    db.add(new_cat)

        db.commit()
        print("Categories seeded successfully")
    except Exception as e:
        print(f"Error seeding categories: {e}")
        db.rollback()
        raise
    for category in predefined_categories:
        existing = db.query(Category).filter(Category.name == category["name"]).first()
        if not existing:
            new_cat = Category(name=category["name"], transaction_type=category["type"])
            db.add(new_cat)
    db.commit()
    db.close()
