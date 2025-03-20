# generate_sample_data.py
import random
import datetime
from dateutil.relativedelta import relativedelta
from app.database import SessionLocal
from app.models import Category, Transaction
from app.schemas import TransactionType, RecurrencePeriod

# Common expense descriptions by category
DESCRIPTIONS = {
    "Transportation": [
        "Gas", "Uber ride", "Car payment", "Bus ticket", "Train pass", "Car maintenance", 
        "Parking fee", "Toll payment", "Car insurance", "Car registration"
    ],
    "Food & Groceries": [
        "Grocery shopping", "Supermarket", "Fresh produce", "Butcher", "Bakery", 
        "Wholesale club", "Farmer's market", "Specialty food store", "Online grocery delivery"
    ],
    "Utilities": [
        "Electricity bill", "Water bill", "Gas bill", "Internet bill", "Phone bill", 
        "Streaming services", "Cable TV", "Trash collection", "Sewer bill"
    ],
    "Healthcare": [
        "Doctor visit", "Prescription", "Dental checkup", "Eye exam", "Medical insurance", 
        "Therapy session", "Urgent care", "Specialist visit", "Medical supplies"
    ],
    "Entertainment": [
        "Movie tickets", "Concert tickets", "Streaming subscription", "Books", "Video games", 
        "Music subscription", "Museum entry", "Theater show", "Sporting event", "Hobby supplies"
    ],
    "Shopping": [
        "Clothing", "Electronics", "Home goods", "Furniture", "Appliances", 
        "Online shopping", "Department store", "Shoes", "Accessories", "Gifts"
    ],
    "Personal Care": [
        "Haircut", "Salon services", "Spa day", "Gym membership", "Cosmetics", 
        "Toiletries", "Supplements", "Wellness products", "Personal trainer"
    ],
    "Education": [
        "Tuition", "Textbooks", "School supplies", "Online course", "Workshop fee", 
        "Professional certification", "Coaching", "Tutoring", "Educational software"
    ],
    "Misc": [
        "Unexpected expense", "Service fee", "Membership dues", "Donation", "Gift", 
        "Subscription", "Repair cost", "Miscellaneous purchase", "Other expense"
    ],
    "Income": [
        "Salary", "Freelance work", "Side gig", "Contract payment", "Bonus", 
        "Commission", "Investment return", "Dividend", "Refund", "Gift received"
    ],
}

# Generate realistic amount ranges for each category
AMOUNT_RANGES = {
    "Transportation": (15, 200),
    "Food & Groceries": (20, 300),
    "Utilities": (50, 250),
    "Healthcare": (25, 500),
    "Entertainment": (10, 150),
    "Shopping": (20, 400),
    "Personal Care": (15, 200),
    "Education": (100, 1000),
    "Misc": (10, 300),
    "Income": (1000, 5000),
}

# Function to generate random date in a given range
def random_date(start_date, end_date):
    time_diff = end_date - start_date
    days_diff = time_diff.days
    random_days = random.randint(0, days_diff)
    return start_date + datetime.timedelta(days=random_days)

def generate_sample_data(num_transactions=100):
    """Generate sample transactions for the personal finance app."""
    # Get database session
    db = SessionLocal()
    
    try:
        # Get all categories from the database
        categories = db.query(Category).all()
        
        if not categories:
            print("No categories found in the database. Please run the application first to seed categories.")
            return
            
        # Define date range for transactions (last 6 months to future 2 months)
        end_date = datetime.date.today() + relativedelta(months=2)
        start_date = datetime.date.today() - relativedelta(months=6)
        
        print(f"Generating {num_transactions} random transactions...")
        
        # Generate random transactions
        for _ in range(num_transactions):
            # Select a random category
            category = random.choice(categories)
            
            # Determine transaction type based on category
            transaction_type = category.transaction_type
            
            # Generate random amount based on category
            category_name = category.name
            min_amount, max_amount = AMOUNT_RANGES.get(category_name, (10, 500))
            
            if transaction_type == TransactionType.EXPENSE:
                amount = round(random.uniform(min_amount, max_amount), 2)
            else:  # INCOME
                amount = round(random.uniform(min_amount, max_amount), 2)
            
            # Generate random date
            date = random_date(start_date, end_date)
            
            # Determine if transaction is recurring (20% probability)
            is_recurring = random.random() < 0.2
            
            # Assign recurrence period if transaction is recurring
            recurrence_period = RecurrencePeriod.NONE
            if is_recurring:
                recurrence_options = [
                    RecurrencePeriod.DAILY,
                    RecurrencePeriod.WEEKLY,
                    RecurrencePeriod.MONTHLY,
                    RecurrencePeriod.YEARLY
                ]
                recurrence_period = random.choice(recurrence_options)
            
            # Generate description based on category
            descriptions = DESCRIPTIONS.get(category_name, ["Transaction"])
            description = random.choice(descriptions)
            
            # Create transaction
            transaction = Transaction(
                amount=amount,
                date=date,
                description=description,
                is_recurring=is_recurring,
                recurrence_period=recurrence_period,
                transaction_type=transaction_type,
                category_id=category.id
            )
            
            db.add(transaction)
        
        # Commit all transactions to the database
        db.commit()
        print(f"Successfully generated {num_transactions} random transactions!")
        
    except Exception as e:
        db.rollback()
        print(f"Error generating sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    # Default number of transactions to generate
    num_transactions = 100
    
    # Check if user provided a number of transactions to generate
    if len(sys.argv) > 1:
        try:
            num_transactions = int(sys.argv[1])
        except ValueError:
            print("Please provide a valid number of transactions to generate.")
            sys.exit(1)
    
    # Generate sample data
    generate_sample_data(num_transactions) 