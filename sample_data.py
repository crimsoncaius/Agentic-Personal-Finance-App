from datetime import datetime, timedelta
import sqlite3
from passlib.context import CryptContext
import random
from enum import Enum

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TransactionType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


def create_sample_data():
    # Connect to database
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email STRING UNIQUE NOT NULL,
            username STRING UNIQUE NOT NULL,
            password_hash STRING NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR NOT NULL,
            transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')),
            user_id INTEGER NOT NULL,
            UNIQUE(name, user_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount FLOAT NOT NULL,
            date DATE DEFAULT CURRENT_DATE,
            description VARCHAR,
            transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')),
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(category_id) REFERENCES categories(id)
        );
    """
    )

    # Sample users data
    sample_users = [
        {
            "email": "john.doe@example.com",
            "username": "johndoe",
            "password": "SecurePass123!",
            "salary": 5000.00,
            "rent": 1500.00,
            "utilities": 200.00,
            "grocery_min": 50,
            "grocery_max": 200,
            "dining_min": 20,
            "dining_max": 100,
        },
        {
            "email": "jane.smith@example.com",
            "username": "janesmith",
            "password": "JanePass456$",
            "salary": 6200.00,
            "rent": 1800.00,
            "utilities": 250.00,
            "grocery_min": 60,
            "grocery_max": 220,
            "dining_min": 25,
            "dining_max": 120,
        },
        {
            "email": "alex.lee@example.com",
            "username": "alexlee",
            "password": "AlexPwd789#",
            "salary": 4300.00,
            "rent": 1200.00,
            "utilities": 180.00,
            "grocery_min": 40,
            "grocery_max": 150,
            "dining_min": 15,
            "dining_max": 80,
        },
    ]

    for user in sample_users:
        # Insert user
        cursor.execute(
            """
            INSERT INTO users (email, username, password_hash, created_at, last_login)
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
            (
                user["email"],
                user["username"],
                pwd_context.hash(user["password"]),
            ),
        )
        user_id = cursor.lastrowid

        # Sample categories
        categories = [
            # Income categories
            ("Salary", TransactionType.INCOME),
            ("Freelance", TransactionType.INCOME),
            ("Investment", TransactionType.INCOME),
            # Expense categories
            ("Housing", TransactionType.EXPENSE),
            ("Utilities", TransactionType.EXPENSE),
            ("Groceries", TransactionType.EXPENSE),
            ("Transportation", TransactionType.EXPENSE),
            ("Healthcare", TransactionType.EXPENSE),
            ("Entertainment", TransactionType.EXPENSE),
            ("Dining Out", TransactionType.EXPENSE),
            ("Shopping", TransactionType.EXPENSE),
            ("Education", TransactionType.EXPENSE),
        ]

        # Insert categories
        category_ids = {}
        for cat_name, cat_type in categories:
            cursor.execute(
                """
                INSERT INTO categories (name, transaction_type, user_id)
                VALUES (?, ?, ?)
            """,
                (cat_name, cat_type, user_id),
            )
            category_ids[cat_name] = cursor.lastrowid

        # Generate 3 months of transactions
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        current_date = start_date

        while current_date <= end_date:
            # Monthly salary (around 15th)
            if current_date.day == 15:
                cursor.execute(
                    """
                    INSERT INTO transactions (amount, date, description, transaction_type, user_id, category_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        user["salary"],
                        current_date,
                        "Monthly Salary",
                        TransactionType.INCOME,
                        user_id,
                        category_ids["Salary"],
                    ),
                )

            # Random daily expenses
            if random.random() < 0.7:  # 70% chance of having expenses on any day
                # Groceries
                if random.random() < 0.3:
                    amount = round(
                        random.uniform(user["grocery_min"], user["grocery_max"]), 2
                    )
                    cursor.execute(
                        """
                        INSERT INTO transactions (amount, date, description, transaction_type, user_id, category_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            amount,
                            current_date,
                            "Grocery shopping",
                            TransactionType.EXPENSE,
                            user_id,
                            category_ids["Groceries"],
                        ),
                    )

                # Dining out
                if random.random() < 0.2:
                    amount = round(
                        random.uniform(user["dining_min"], user["dining_max"]), 2
                    )
                    cursor.execute(
                        """
                        INSERT INTO transactions (amount, date, description, transaction_type, user_id, category_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            amount,
                            current_date,
                            "Restaurant",
                            TransactionType.EXPENSE,
                            user_id,
                            category_ids["Dining Out"],
                        ),
                    )

            # Monthly fixed expenses
            if current_date.day == 1:
                # Rent
                cursor.execute(
                    """
                    INSERT INTO transactions (amount, date, description, transaction_type, user_id, category_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        user["rent"],
                        current_date,
                        "Monthly Rent",
                        TransactionType.EXPENSE,
                        user_id,
                        category_ids["Housing"],
                    ),
                )

                # Utilities
                cursor.execute(
                    """
                    INSERT INTO transactions (amount, date, description, transaction_type, user_id, category_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        user["utilities"],
                        current_date,
                        "Utilities",
                        TransactionType.EXPENSE,
                        user_id,
                        category_ids["Utilities"],
                    ),
                )

            current_date += timedelta(days=1)

    # Commit changes and close connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_sample_data()
