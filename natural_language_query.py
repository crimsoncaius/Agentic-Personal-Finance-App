import os
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_db_connection():
    """Create a database connection."""
    return sqlite3.connect("finance.db")


def execute_sql_query(query):
    """Execute SQL query and return results."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    finally:
        conn.close()


def get_categories():
    """Fetch all categories from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name, transaction_type FROM categories ORDER BY name")
        categories = cursor.fetchall()
        return categories
    finally:
        conn.close()


def convert_to_sql(natural_language_query):
    """Convert natural language query to SQL using OpenAI."""
    # Get current categories
    categories = get_categories()

    # Build categories section of the prompt
    categories_section = "Current categories in the database:\n"
    if categories:
        for name, trans_type in categories:
            categories_section += f"- {name} ({trans_type})\n"
    else:
        categories_section += "No categories defined yet.\n"

    system_prompt = f"""You are a SQL expert. Convert the given natural language query into SQL.
    The database schema has the following tables and relationships:

    Table: categories
    - id (INTEGER, PRIMARY KEY, NOT NULL)
    - name (VARCHAR, NOT NULL, UNIQUE)
    - transaction_type (VARCHAR(7), NOT NULL) - Must be 'INCOME' or 'EXPENSE' (uppercase)

    Table: transactions
    - id (INTEGER, PRIMARY KEY, NOT NULL)
    - amount (FLOAT, NOT NULL)
    - date (DATE)
    - description (VARCHAR)
    - is_recurring (BOOLEAN)
    - recurrence_period (VARCHAR(7)) - Can be 'daily', 'weekly', 'monthly', 'yearly'
    - transaction_type (VARCHAR(7), NOT NULL) - Must be 'INCOME' or 'EXPENSE' (uppercase)
    - category_id (INTEGER, FOREIGN KEY REFERENCES categories(id))

    Important relationships:
    - transactions.category_id is a foreign key to categories.id
    - Each transaction must have a transaction_type ('INCOME' or 'EXPENSE')
    - Each category must have a transaction_type ('INCOME' or 'EXPENSE')
    - Category names are unique
    - If a transaction is recurring (is_recurring = true), it must have a recurrence_period

    {categories_section}

    Return ONLY the SQL query without any explanation or additional text."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": natural_language_query},
        ],
    )

    return response.choices[0].message.content.strip()


def main():
    print("Welcome to the Natural Language Finance Query System!")
    print("Type 'exit' to quit.")

    while True:
        query = input("\nEnter your question: ")
        if query.lower() == "exit":
            break

        try:
            # Convert natural language to SQL
            sql_query = convert_to_sql(query)
            print("\nGenerated SQL Query:")
            print(sql_query)

            # Execute the query
            results = execute_sql_query(sql_query)

            # Print results
            print("\nResults:")
            for row in results:
                print(row)

        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
