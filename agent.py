import os
import sqlite3
import re
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from datetime import date

# --------------------------------------------------------------------
# 1. DB UTILITIES
# --------------------------------------------------------------------


def get_db_connection():
    """Create and return a SQLite database connection."""
    return sqlite3.connect("finance.db", timeout=10)


def execute_sql_query(query: str, operation_type: str = "query"):
    """Execute a SQL query and return results (for SELECT) or rowcount (for mutations)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cleaned_query = re.sub(
            r"^```sql\s*|\s*```$", "", query, flags=re.MULTILINE
        ).strip()

        if operation_type in ["update", "delete"]:
            if "where" not in cleaned_query.lower():
                conn.close()
                raise RuntimeError(
                    f"Safety Error: {operation_type.upper()} statement without a WHERE clause detected.\nQuery: {query}"
                )

        cursor.execute(cleaned_query)

        if operation_type == "view":
            results = cursor.fetchall()
            conn.close()
            return results
        else:  # create, update, delete
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return affected
    except sqlite3.Error as e:
        conn.close()
        raise RuntimeError(f"Database error: {str(e)}\nQuery: {query}")


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


# --------------------------------------------------------------------
# 2. OPENAI CLIENT + HELPER FOR PROMPTS
# --------------------------------------------------------------------

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables or .env file")
client = OpenAI(api_key=api_key)


def generate_sql_with_llm(system_prompt: str, user_message: str) -> str:
    """
    General helper to call OpenAI ChatCompletion with a system prompt + user message.
    Returns the generated SQL statement as a string.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
        )
        sql_query = response.choices[0].message.content.strip()
        cleaned_sql_query = re.sub(
            r"^```sql\s*|\s*```$", "", sql_query, flags=re.MULTILINE
        ).strip()
        return cleaned_sql_query
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "-- Error generating SQL --"


# --------------------------------------------------------------------
# 3. INTENT CLASSIFICATION
# --------------------------------------------------------------------


def classify_crud_intent(user_input: str) -> str:
    """
    Use LLM to classify user intent into create, view, update, or delete.
    """
    system_prompt = """You are an expert at classifying user intentions in a financial management system.
    Given a user's input, classify if they want to:
    1. Create new data (e.g., add transaction, new category) -> return "create"
    2. View/read existing data (e.g., show transactions, list categories, total spending) -> return "view"
    3. Update existing data (e.g., change description, modify amount) -> return "update"
    4. Delete existing data (e.g., remove transaction) -> return "delete"

    Return ONLY the word "create", "view", "update", or "delete" with no additional text or explanation."""

    valid_intents = ["create", "view", "update", "delete"]
    default_intent = "view"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            temperature=0.0,
        )
        intent = response.choices[0].message.content.strip().lower()

        if intent in valid_intents:
            return intent
        else:
            print(
                f"Warning: Unexpected intent classification '{intent}'. Defaulting to '{default_intent}'."
            )
            return default_intent
    except Exception as e:
        print(
            f"Error during intent classification: {e}. Defaulting to '{default_intent}'."
        )
        return default_intent


# --------------------------------------------------------------------
# 4. NODES / FLOWS
# --------------------------------------------------------------------


class BaseNode:
    def _detect_category_usage(self, text: str) -> bool:
        return "category" in text.lower()

    def _build_categories_context(self) -> str:
        try:
            categories = get_categories()
            if not categories:
                return "No categories defined yet."
            context_lines = ["Current categories:"]
            for name, ttype in categories:
                context_lines.append(f" - {name} ({ttype})")
            return "\n".join(context_lines)
        except Exception as e:
            print(f"Warning: Failed to build categories context: {e}")
            return "Could not retrieve category list."


class ViewNode(BaseNode):
    """Handles read-only view/query requests for SQLite."""

    def run(self, user_input: str) -> None:
        current_date_str = date.today().isoformat()  # Get current date as YYYY-MM-DD
        need_categories_context = self._detect_category_usage(user_input)
        categories_context = (
            self._build_categories_context() if need_categories_context else ""
        )

        system_prompt = f"""
        You are a world-class SQL expert specifically for **SQLite** databases.
        The user wants to view or query existing data.
        **The current date is {current_date_str}.** Use this to resolve relative dates like 'today', 'yesterday', 'last month'.
        Ensure all generated SQL syntax is compatible with **SQLite**.

        Database Schema:
        Table: categories (id INTEGER PK, name VARCHAR UNIQUE, transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')))
        Table: transactions (id INTEGER PK, amount FLOAT, date DATE, description VARCHAR, transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')), category_id INTEGER FK REFERENCES categories(id))

        {categories_context}

        **SQLite Date/Time Guidance:** Use `date()`, `strftime()`, 'now', '+X days', 'start of month', etc. Use `date('{current_date_str}')` if you need today's date literal. **Do not use** `DATE_TRUNC`, `INTERVAL`.

        Return ONLY the SQL query (SELECT) that answers the user request, formatted for **SQLite**. No explanations or markdown.
        """
        sql_query = generate_sql_with_llm(system_prompt, user_input)
        print(f"\n[ViewNode] Generated SQL:\n{sql_query}")

        if sql_query == "-- Error generating SQL --":
            print("[ViewNode] Skipping execution due to SQL generation error.")
            return
        try:
            results = execute_sql_query(sql_query, operation_type="view")
            print("\n[ViewNode] Results:")
            if results:
                for row in results:
                    print(row)
            else:
                print("No results found.")
        except RuntimeError as e:
            print(f"[ViewNode] Error executing query: {str(e)}")


class CreateNode(BaseNode):
    """Handles create/insert requests for SQLite."""

    def run(self, user_input: str) -> None:
        current_date_str = date.today().isoformat()
        need_categories_context = self._detect_category_usage(user_input)
        categories_context = (
            self._build_categories_context() if need_categories_context else ""
        )

        system_prompt = f"""
        You are a world-class SQL expert specifically for **SQLite** databases.
        The user wants to create a new record (transaction or category).
        **The current date is {current_date_str}.** Use this to resolve relative dates like 'today', 'yesterday'.
        Ensure all generated SQL syntax is compatible with **SQLite**.

        Database Schema:
        Table: categories (id INTEGER PK, name VARCHAR UNIQUE, transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')))
        Table: transactions (id INTEGER PK, amount FLOAT, date DATE, description VARCHAR, transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')), category_id INTEGER FK REFERENCES categories(id))

        {categories_context}

        **SQLite Date/Time Guidance:** Use `date('{current_date_str}')` for today, `date('{current_date_str}', '-1 day')` for yesterday. Use `date()` function generally.

        **Category Handling for INSERT transactions:**
        1. If user explicitly mentions a category name from 'Current categories', use subquery `(SELECT id FROM categories WHERE name = 'ExplicitCategoryName')`.
        2. If no category mentioned, analyze description. If it matches a category (e.g., 'lunch' -> 'Food & Groceries'), use subquery `(SELECT id FROM categories WHERE name = 'InferredCategoryName')`.
        3. If no match/inference, use `(SELECT id FROM categories WHERE name = 'Misc')` as fallback. Ensure 'Misc' exists.

        Return ONLY the SQL statement (INSERT) formatted for **SQLite**. Use 0/1 for booleans. No explanations or markdown.
        """
        sql_query = generate_sql_with_llm(system_prompt, user_input)
        print(f"\n[CreateNode] Generated SQL:\n{sql_query}")

        if sql_query == "-- Error generating SQL --":
            print("[CreateNode] Skipping execution due to SQL generation error.")
            return
        try:
            if not sql_query.lower().startswith("insert"):
                print("[CreateNode] Error: Generated SQL is not an INSERT statement.")
                return
            affected = execute_sql_query(sql_query, operation_type="create")
            print(f"[CreateNode] Rows affected: {affected}")
        except RuntimeError as e:
            print(f"[CreateNode] Error executing insert: {str(e)}")


class UpdateNode(BaseNode):
    """Handles update requests for SQLite."""

    def run(self, user_input: str) -> None:
        current_date_str = date.today().isoformat()
        need_categories_context = self._detect_category_usage(user_input)
        categories_context = (
            self._build_categories_context() if need_categories_context else ""
        )

        system_prompt = f"""
        You are a world-class SQL expert specifically for **SQLite** databases.
        The user wants to update an existing record (likely a transaction).
        **The current date is {current_date_str}.** This might be relevant if updating date fields.
        Ensure all generated SQL syntax is compatible with **SQLite**.

        Database Schema:
        Table: categories (id INTEGER PK, name VARCHAR UNIQUE, transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')))
        Table: transactions (id INTEGER PK, amount FLOAT, date DATE, description VARCHAR, transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')), category_id INTEGER FK REFERENCES categories(id))

        {categories_context}

        **CRITICAL:** Generated UPDATE statements **MUST** include a `WHERE` clause to target the specific record(s) to update (usually by `id`). Infer the target record ID from the user request if possible (e.g., "transaction id 10"). If no target is clear, the query will likely fail safety checks.

        **SQLite Date/Time Guidance:** Use `date('{current_date_str}')` if needed for today's date.

        Return ONLY the SQL statement (UPDATE) formatted for **SQLite**. Use 0/1 for booleans. No explanations or markdown.
        """
        sql_query = generate_sql_with_llm(system_prompt, user_input)
        print(f"\n[UpdateNode] Generated SQL:\n{sql_query}")

        if sql_query == "-- Error generating SQL --":
            print("[UpdateNode] Skipping execution due to SQL generation error.")
            return
        try:
            if not sql_query.lower().startswith("update"):
                print("[UpdateNode] Error: Generated SQL is not an UPDATE statement.")
                return
            affected = execute_sql_query(sql_query, operation_type="update")
            print(f"[UpdateNode] Rows affected: {affected}")
        except RuntimeError as e:
            print(f"[UpdateNode] Error executing update: {str(e)}")


class DeleteNode(BaseNode):
    """Handles delete requests for SQLite."""

    def run(self, user_input: str) -> None:
        current_date_str = date.today().isoformat()
        categories_context = (
            self._build_categories_context()
            if self._detect_category_usage(user_input)
            else ""
        )

        system_prompt = f"""
        You are a world-class SQL expert specifically for **SQLite** databases.
        The user wants to delete an existing record (likely a transaction).
        **The current date is {current_date_str}.** This might be relevant if the request involves dates (e.g., "delete transactions from last week").
        Ensure all generated SQL syntax is compatible with **SQLite**.

        Database Schema:
        Table: categories (id INTEGER PK, name VARCHAR UNIQUE, transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')))
        Table: transactions (id INTEGER PK, amount FLOAT, date DATE, description VARCHAR, transaction_type VARCHAR(7) CHECK(transaction_type IN ('INCOME', 'EXPENSE')), category_id INTEGER FK REFERENCES categories(id))

        {categories_context}

        **CRITICAL:** Generated DELETE statements **MUST** include a `WHERE` clause to target the specific record(s) to delete (usually by `id`). Infer the target record ID from the user request (e.g., "transaction id 15"). If no target is clear, the query will likely fail safety checks.

        **SQLite Date/Time Guidance:** Use `date('{current_date_str}')` if needed for today's date. Use `date()` and `strftime()` for conditions.

        Return ONLY the SQL statement (DELETE) formatted for **SQLite**. No explanations or markdown.
        """
        sql_query = generate_sql_with_llm(system_prompt, user_input)
        print(f"\n[DeleteNode] Generated SQL:\n{sql_query}")

        if sql_query == "-- Error generating SQL --":
            print("[DeleteNode] Skipping execution due to SQL generation error.")
            return
        try:
            if not sql_query.lower().startswith("delete"):
                print("[DeleteNode] Error: Generated SQL is not a DELETE statement.")
                return
            affected = execute_sql_query(sql_query, operation_type="delete")
            print(f"[DeleteNode] Rows affected: {affected}")
        except RuntimeError as e:
            print(f"[DeleteNode] Error executing delete: {str(e)}")


# --------------------------------------------------------------------
# 5. MAIN APPLICATION FLOW
# --------------------------------------------------------------------


def main():
    print("Welcome to the Finance Assistant! Type 'exit' to quit.\n")

    # Optional DB check
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categories';"
        )
        if not cursor.fetchone():
            print("Warning: 'categories' table not found.")
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';"
        )
        if not cursor.fetchone():
            print("Warning: 'transactions' table not found.")
        conn.close()
    except Exception as e:
        print(f"Warning: Could not verify database tables: {e}")

    # Instantiate nodes
    view_node = ViewNode()
    create_node = CreateNode()
    update_node = UpdateNode()
    delete_node = DeleteNode()

    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            if not user_input.strip():
                continue

            # Classify intent into CRUD
            intent = classify_crud_intent(user_input)
            print(f"[Intent Classified As: {intent}]")  # Log the classified intent

            # Route to the appropriate node
            if intent == "view":
                view_node.run(user_input)
            elif intent == "create":
                create_node.run(user_input)
            elif intent == "update":
                update_node.run(user_input)
            elif intent == "delete":
                delete_node.run(user_input)
            else:
                print(f"Error: Unhandled intent '{intent}'. Please rephrase.")

        except EOFError:
            print("\nGoodbye!")
            break
        except KeyboardInterrupt:
            print("\nOperation cancelled. Type 'exit' to quit.")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
