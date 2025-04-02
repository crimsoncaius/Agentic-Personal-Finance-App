from sqlalchemy import create_engine, text
from .database import SQLALCHEMY_DATABASE_URL
from .models import User
from .init_db import seed_categories


def migrate_database():
    """Migrate the database to support multi-user functionality"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    with engine.connect() as connection:
        # Create users table if it doesn't exist
        connection.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR NOT NULL UNIQUE,
                username VARCHAR NOT NULL UNIQUE,
                password_hash VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """
            )
        )

        # Create default user if no users exist
        result = connection.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if result == 0:
            default_user = User(
                email="default@example.com",
                username="default_user",
                password_hash=User.hash_password("default_password"),
            )
            connection.execute(
                text(
                    """
                INSERT INTO users (email, username, password_hash)
                VALUES (:email, :username, :password_hash)
            """
                ),
                {
                    "email": default_user.email,
                    "username": default_user.username,
                    "password_hash": default_user.password_hash,
                },
            )
            print("Created default user")

        # Get default user id
        default_user_id = connection.execute(
            text("SELECT id FROM users WHERE email = 'default@example.com'")
        ).scalar()

        # Handle categories table
        try:
            # Drop old unique constraint if it exists
            try:
                connection.execute(text("DROP INDEX IF EXISTS ix_categories_name"))
                print("Dropped old unique index on categories.name")
            except:
                print("No old unique index to drop")

            # Check if categories table exists
            connection.execute(text("SELECT 1 FROM categories LIMIT 1"))
            print("Categories table exists, adding user_id column if needed")

            # Add user_id column if it doesn't exist
            try:
                connection.execute(
                    text("ALTER TABLE categories ADD COLUMN user_id INTEGER")
                )
                print("Added user_id column to categories")
            except:
                print("user_id column already exists in categories")

            # Update existing categories to belong to default user
            connection.execute(
                text(
                    """
                UPDATE categories 
                SET user_id = :user_id
                WHERE user_id IS NULL
                """
                ),
                {"user_id": default_user_id},
            )
            print("Updated existing categories to belong to default user")

        except Exception as e:
            print(f"Categories table doesn't exist or other error: {e}")
            # Create categories table with user_id and proper unique constraint
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL,
                    transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')),
                    user_id INTEGER NOT NULL,
                    UNIQUE(name, user_id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
                )
            )
            print("Created new categories table with user_id")

        # Add the new unique constraint for name+user_id if it doesn't exist
        try:
            connection.execute(
                text(
                    """
                CREATE UNIQUE INDEX IF NOT EXISTS uix_category_name_user 
                ON categories(name, user_id)
                """
                )
            )
            print("Added unique constraint on (name, user_id)")
        except:
            print("Unique constraint on (name, user_id) already exists")

        # Handle transactions table
        try:
            # Check if transactions table exists
            connection.execute(text("SELECT 1 FROM transactions LIMIT 1"))
            print("Transactions table exists, adding user_id column if needed")

            # Add user_id column if it doesn't exist
            try:
                connection.execute(
                    text("ALTER TABLE transactions ADD COLUMN user_id INTEGER")
                )
                print("Added user_id column to transactions")
            except:
                print("user_id column already exists in transactions")

            # Update existing transactions to belong to default user
            connection.execute(
                text(
                    """
                UPDATE transactions 
                SET user_id = :user_id
                WHERE user_id IS NULL
                """
                ),
                {"user_id": default_user_id},
            )
            print("Updated existing transactions to belong to default user")

        except Exception as e:
            print(f"Transactions table doesn't exist or other error: {e}")
            # Create transactions table with user_id
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount FLOAT NOT NULL,
                    date DATE DEFAULT CURRENT_DATE,
                    description VARCHAR,
                    is_recurring BOOLEAN DEFAULT FALSE,
                    recurrence_period VARCHAR(7) DEFAULT 'NONE' CHECK(recurrence_period IN ('NONE', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY')),
                    transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')),
                    user_id INTEGER NOT NULL,
                    category_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(category_id) REFERENCES categories(id)
                )
                """
                )
            )
            print("Created new transactions table with user_id")

        # Add foreign key constraints if they don't exist
        try:
            connection.execute(
                text(
                    """
                ALTER TABLE categories 
                ADD CONSTRAINT fk_categories_user 
                FOREIGN KEY (user_id) REFERENCES users(id)
                """
                )
            )
            print("Added foreign key constraint to categories")
        except:
            print("Categories foreign key constraint already exists")

        try:
            connection.execute(
                text(
                    """
                ALTER TABLE transactions 
                ADD CONSTRAINT fk_transactions_user 
                FOREIGN KEY (user_id) REFERENCES users(id)
                """
                )
            )
            print("Added foreign key constraint to transactions")
        except:
            print("Transactions foreign key constraint already exists")

        connection.commit()

    # After migration, seed categories for all users
    try:
        seed_categories()
        print("Seeded categories for all users")
    except Exception as e:
        print(f"Error seeding categories: {e}")


if __name__ == "__main__":
    migrate_database()
