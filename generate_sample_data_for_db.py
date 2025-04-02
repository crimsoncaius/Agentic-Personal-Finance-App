# generate_sample_data.py
import random
import datetime
from dateutil.relativedelta import relativedelta
from backend.database import SessionLocal
from backend.models import Category, Transaction, User
from backend.schemas import TransactionType, RecurrencePeriod
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common expense descriptions by category
DESCRIPTIONS = {
    "Transportation": [
        "Gas",
        "Uber ride",
        "Car payment",
        "Bus ticket",
        "Train pass",
        "Car maintenance",
        "Parking fee",
        "Toll payment",
        "Car insurance",
        "Car registration",
    ],
    "Food & Groceries": [
        "Grocery shopping",
        "Supermarket",
        "Fresh produce",
        "Butcher",
        "Bakery",
        "Wholesale club",
        "Farmer's market",
        "Specialty food store",
        "Online grocery delivery",
    ],
    "Utilities": [
        "Electricity bill",
        "Water bill",
        "Gas bill",
        "Internet bill",
        "Phone bill",
        "Streaming services",
        "Cable TV",
        "Trash collection",
        "Sewer bill",
    ],
    "Healthcare": [
        "Doctor visit",
        "Prescription",
        "Dental checkup",
        "Eye exam",
        "Medical insurance",
        "Therapy session",
        "Urgent care",
        "Specialist visit",
        "Medical supplies",
    ],
    "Entertainment": [
        "Movie tickets",
        "Concert tickets",
        "Streaming subscription",
        "Books",
        "Video games",
        "Music subscription",
        "Museum entry",
        "Theater show",
        "Sporting event",
        "Hobby supplies",
    ],
    "Shopping": [
        "Clothing",
        "Electronics",
        "Home goods",
        "Furniture",
        "Appliances",
        "Online shopping",
        "Department store",
        "Shoes",
        "Accessories",
        "Gifts",
    ],
    "Personal Care": [
        "Haircut",
        "Salon services",
        "Spa day",
        "Gym membership",
        "Cosmetics",
        "Toiletries",
        "Supplements",
        "Wellness products",
        "Personal trainer",
    ],
    "Education": [
        "Tuition",
        "Textbooks",
        "School supplies",
        "Online course",
        "Workshop fee",
        "Professional certification",
        "Coaching",
        "Tutoring",
        "Educational software",
    ],
    "Misc": [
        "Unexpected expense",
        "Service fee",
        "Membership dues",
        "Donation",
        "Gift",
        "Subscription",
        "Repair cost",
        "Miscellaneous purchase",
        "Other expense",
    ],
    "Income": [
        "Salary",
        "Freelance work",
        "Side gig",
        "Contract payment",
        "Bonus",
        "Commission",
        "Investment return",
        "Dividend",
        "Refund",
        "Gift received",
    ],
}

# User profiles with their specific amount ranges and transaction patterns
USER_PROFILES = {
    "professional": {
        "email": "professional@example.com",
        "username": "professional_user",
        "password": "prof123secure",
        "num_transactions": (150, 200),
        "amounts": {
            "Transportation": (30, 300),
            "Food & Groceries": (50, 400),
            "Utilities": (100, 400),
            "Healthcare": (50, 1000),
            "Entertainment": (50, 500),
            "Shopping": (100, 1000),
            "Personal Care": (50, 400),
            "Education": (200, 2000),
            "Misc": (50, 500),
            "Income": (5000, 12000),
        },
        "recurring_probability": 0.3,
    },
    "student": {
        "email": "student@example.com",
        "username": "student_user",
        "password": "student123secure",
        "num_transactions": (50, 80),
        "amounts": {
            "Transportation": (10, 100),
            "Food & Groceries": (20, 150),
            "Utilities": (50, 150),
            "Healthcare": (20, 200),
            "Entertainment": (10, 50),
            "Shopping": (20, 200),
            "Personal Care": (10, 100),
            "Education": (500, 3000),
            "Misc": (10, 100),
            "Income": (500, 2000),
        },
        "recurring_probability": 0.1,
    },
    "family": {
        "email": "family@example.com",
        "username": "family_user",
        "password": "family123secure",
        "num_transactions": (200, 250),
        "amounts": {
            "Transportation": (50, 500),
            "Food & Groceries": (100, 800),
            "Utilities": (150, 500),
            "Healthcare": (50, 1000),
            "Entertainment": (50, 300),
            "Shopping": (50, 1000),
            "Personal Care": (30, 300),
            "Education": (100, 2000),
            "Misc": (50, 500),
            "Income": (7000, 15000),
        },
        "recurring_probability": 0.4,
    },
    "freelancer": {
        "email": "freelancer@example.com",
        "username": "freelancer_user",
        "password": "freelance123secure",
        "num_transactions": (100, 150),
        "amounts": {
            "Transportation": (20, 200),
            "Food & Groceries": (30, 300),
            "Utilities": (80, 300),
            "Healthcare": (50, 800),
            "Entertainment": (30, 200),
            "Shopping": (50, 500),
            "Personal Care": (30, 200),
            "Education": (100, 1000),
            "Misc": (30, 300),
            "Income": (1000, 8000),
        },
        "recurring_probability": 0.2,
    },
    "retiree": {
        "email": "retiree@example.com",
        "username": "retiree_user",
        "password": "retiree123secure",
        "num_transactions": (80, 100),
        "amounts": {
            "Transportation": (20, 200),
            "Food & Groceries": (100, 400),
            "Utilities": (100, 300),
            "Healthcare": (100, 1000),
            "Entertainment": (50, 400),
            "Shopping": (50, 400),
            "Personal Care": (50, 300),
            "Education": (20, 200),
            "Misc": (50, 300),
            "Income": (2000, 5000),
        },
        "recurring_probability": 0.5,
    },
}


def random_date(start_date, end_date):
    """Generate random date in a given range."""
    time_diff = end_date - start_date
    days_diff = time_diff.days
    random_days = random.randint(0, days_diff)
    return start_date + datetime.timedelta(days=random_days)


def create_test_user(db, profile_data):
    """Create a test user if they don't exist."""
    try:
        # Check if user exists
        existing_user = (
            db.query(User).filter(User.email == profile_data["email"]).first()
        )
        if existing_user:
            logger.info(f"User {profile_data['email']} already exists")
            return existing_user

        # Create new user
        user = User(
            email=profile_data["email"],
            username=profile_data["username"],
            password_hash=User.hash_password(profile_data["password"]),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created test user: {user.email}")
        return user
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        db.rollback()
        return None


def generate_user_transactions(db, user, profile_data, categories):
    """Generate transactions for a specific user based on their profile."""
    try:
        # Define date range (last 6 months to future 2 months)
        end_date = datetime.date.today() + relativedelta(months=2)
        start_date = datetime.date.today() - relativedelta(months=6)

        # Get number of transactions to generate
        num_transactions = random.randint(*profile_data["num_transactions"])
        logger.info(f"Generating {num_transactions} transactions for {user.email}")

        # Generate transactions
        for _ in range(num_transactions):
            # Select a random category
            category = random.choice(categories)

            # Get amount range based on category and user profile
            min_amount, max_amount = profile_data["amounts"].get(
                category.name, (10, 500)
            )
            amount = round(random.uniform(min_amount, max_amount), 2)

            # Determine if transaction is recurring
            is_recurring = random.random() < profile_data["recurring_probability"]

            # Set recurrence period if recurring
            recurrence_period = RecurrencePeriod.NONE
            if is_recurring:
                recurrence_period = random.choice(
                    [
                        RecurrencePeriod.DAILY,
                        RecurrencePeriod.WEEKLY,
                        RecurrencePeriod.MONTHLY,
                        RecurrencePeriod.YEARLY,
                    ]
                )

            # Generate description
            description = random.choice(
                DESCRIPTIONS.get(category.name, ["Transaction"])
            )

            # Create transaction
            transaction = Transaction(
                amount=amount,
                date=random_date(start_date, end_date),
                description=description,
                is_recurring=is_recurring,
                recurrence_period=recurrence_period,
                transaction_type=category.transaction_type,
                category_id=category.id,
                user_id=user.id,
            )

            db.add(transaction)

        db.commit()
        logger.info(f"Successfully generated transactions for {user.email}")

    except Exception as e:
        logger.error(f"Error generating transactions for {user.email}: {e}")
        db.rollback()


def generate_sample_data():
    """Generate sample data for test users and existing users."""
    db = SessionLocal()

    try:
        # Get all categories
        categories = db.query(Category).all()
        if not categories:
            logger.error(
                "No categories found. Please run the application first to seed categories."
            )
            return

        # Create and generate data for test users
        for profile_name, profile_data in USER_PROFILES.items():
            user = create_test_user(db, profile_data)
            if user:
                generate_user_transactions(db, user, profile_data, categories)

        # Generate data for existing users (excluding test users)
        existing_users = (
            db.query(User)
            .filter(~User.email.in_([p["email"] for p in USER_PROFILES.values()]))
            .all()
        )

        default_profile = {
            "num_transactions": (80, 120),
            "amounts": USER_PROFILES["professional"]["amounts"],
            "recurring_probability": 0.2,
        }

        for user in existing_users:
            logger.info(f"Generating data for existing user: {user.email}")
            generate_user_transactions(db, user, default_profile, categories)

        logger.info("Sample data generation completed successfully!")

    except Exception as e:
        logger.error(f"Error in sample data generation: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    generate_sample_data()
