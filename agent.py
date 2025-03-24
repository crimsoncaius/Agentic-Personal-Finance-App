import os
import sqlite3
import re
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# --------------------------------------------------------------------
# 1. DB UTILITIES
# --------------------------------------------------------------------


def get_db_connection():
    """Create and return a SQLite database connection."""
    return sqlite3.connect("finance.db")


def execute_sql_query(query: str):
    """Execute a SQL query and return results (for SELECT) or rowcount (for mutations)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        # For SELECT queries, return all rows
        if query.strip().lower().startswith("select"):
            results = cursor.fetchall()
            conn.close()
            return results
        else:
            # For mutations, commit and return rowcount
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return affected
    except sqlite3.Error as e:
        conn.close()
        raise RuntimeError(f"Database error: {str(e)}")


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

load_dotenv()  # Make sure your .env has OPENAI_API_KEY
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_sql_with_llm(system_prompt: str, user_message: str) -> str:
    """
    General helper to call OpenAI ChatCompletion with a system prompt + user message.
    Returns the generated SQL statement as a string.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    sql_query = response.choices[0].message.content.strip()
    return sql_query


# --------------------------------------------------------------------
# 3. INTENT CLASSIFICATION
# --------------------------------------------------------------------


def classify_intent(user_input: str) -> str:
    """
    Use LLM to classify if user wants to query (read) or mutate (create/update/delete) data.
    """
    system_prompt = """You are an expert at classifying user intentions in a financial management system.
    Given a user's input, classify if they want to:
    1. Query/read existing data (return "query")
    2. Modify data through creation, updates, or deletions (return "mutation")
    
    Return ONLY the word "query" or "mutation" with no additional text or explanation."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
    )

    intent = response.choices[0].message.content.strip().lower()
    if intent not in ["query", "mutation"]:
        # Fallback to query if LLM gives unexpected response
        return "query"
    return intent


# --------------------------------------------------------------------
# 4. NODES / FLOWS (PSEUDO-LANGGRAPH)
# --------------------------------------------------------------------


class QueryNode:
    """
    Handles read-only queries.
    """

    def __init__(self):
        pass

    def run(self, user_input: str) -> None:
        """
        Convert the natural language query into SQL,
        execute it, and print the results.
        """
        # Potentially decide if categories are needed
        need_categories_context = self._detect_category_usage(user_input)
        categories_context = (
            self._build_categories_context() if need_categories_context else ""
        )

        system_prompt = f"""
        You are a world-class SQL expert. 
        The database schema is:

        Table: categories
        - id (INTEGER, PRIMARY KEY, NOT NULL)
        - name (VARCHAR, NOT NULL, UNIQUE)
        - transaction_type (VARCHAR(7), NOT NULL)  -- Must be 'INCOME' or 'EXPENSE'

        Table: transactions
        - id (INTEGER, PRIMARY KEY, NOT NULL)
        - amount (FLOAT, NOT NULL)
        - date (DATE)
        - description (VARCHAR)
        - is_recurring (BOOLEAN)
        - recurrence_period (VARCHAR(7)) -- 'daily', 'weekly', 'monthly', 'yearly'
        - transaction_type (VARCHAR(7), NOT NULL) -- 'INCOME' or 'EXPENSE'
        - category_id (INTEGER, FOREIGN KEY REFERENCES categories(id))

        {categories_context}

        Return ONLY the SQL query (SELECT) that answers the user request:
        """

        sql_query = generate_sql_with_llm(system_prompt, user_input)
        print(f"\n[QueryNode] Generated SQL:\n{sql_query}")

        # Execute the query
        try:
            results = execute_sql_query(sql_query)
            print("\n[QueryNode] Results:")
            for row in results:
                print(row)
        except RuntimeError as e:
            print(f"[QueryNode] Error executing query: {str(e)}")

    def _detect_category_usage(self, text: str) -> bool:
        """
        Naive: if user mentions 'category' or known category by name, we might pass the categories list.
        """
        # Very rough approach, adjust as needed
        return "category" in text.lower()

    def _build_categories_context(self) -> str:
        """
        Build a text snippet with the existing categories, to include in the system prompt.
        """
        categories = get_categories()
        if not categories:
            return "No categories defined yet."
        context_lines = ["Current categories:"]
        for name, ttype in categories:
            context_lines.append(f" - {name} ({ttype})")
        return "\n".join(context_lines)


class MutationNode:
    """
    Handles create, update, delete statements.
    """

    def __init__(self):
        pass

    def run(self, user_input: str) -> None:
        """
        Convert the natural language input into a suitable INSERT/UPDATE/DELETE,
        execute it, and report results.
        """
        # Possibly refine this to decide if you need categories context
        need_categories_context = self._detect_category_usage(user_input)
        categories_context = (
            self._build_categories_context() if need_categories_context else ""
        )

        system_prompt = f"""
        You are a world-class SQL expert. 
        The database schema is:

        Table: categories
        - id (INTEGER, PRIMARY KEY, NOT NULL)
        - name (VARCHAR, NOT NULL, UNIQUE)
        - transaction_type (VARCHAR(7), NOT NULL)  -- Must be 'INCOME' or 'EXPENSE'

        Table: transactions
        - id (INTEGER, PRIMARY KEY, NOT NULL)
        - amount (FLOAT, NOT NULL)
        - date (DATE)
        - description (VARCHAR)
        - is_recurring (BOOLEAN)
        - recurrence_period (VARCHAR(7)) -- 'daily', 'weekly', 'monthly', 'yearly'
        - transaction_type (VARCHAR(7), NOT NULL) -- 'INCOME' or 'EXPENSE'
        - category_id (INTEGER, FOREIGN KEY REFERENCES categories(id))

        {categories_context}

        The user wants to create, update, or delete records.
        Return ONLY the SQL statement (INSERT, UPDATE, or DELETE).
        """

        sql_query = generate_sql_with_llm(system_prompt, user_input)
        print(f"\n[MutationNode] Generated SQL:\n{sql_query}")

        # Sanity check: We can do an additional safety check here (e.g., disallow DROP TABLE)
        # For example:
        dangerous_keywords = ["drop table", "alter table"]
        if any(kw in sql_query.lower() for kw in dangerous_keywords):
            print("[MutationNode] Aborted - potentially dangerous SQL detected.")
            return

        # Execute the mutation
        try:
            affected = execute_sql_query(sql_query)
            print(f"[MutationNode] Rows affected: {affected}")
        except RuntimeError as e:
            print(f"[MutationNode] Error executing mutation: {str(e)}")

    def _detect_category_usage(self, text: str) -> bool:
        return "category" in text.lower()

    def _build_categories_context(self) -> str:
        categories = get_categories()
        if not categories:
            return "No categories defined yet."
        context_lines = ["Current categories:"]
        for name, ttype in categories:
            context_lines.append(f" - {name} ({ttype})")
        return "\n".join(context_lines)


# --------------------------------------------------------------------
# 5. SAMPLE GRAPH-LIKE FLOW
# --------------------------------------------------------------------


class IntentClassificationNode:
    """
    Uses LLM to classify if user wants 'query' or 'mutation'.
    """

    def run(self, user_input: str) -> str:
        return classify_intent(user_input)


# If you were using a library like LangGraph, you'd define a Graph structure with:
# - an edge from IntentClassificationNode -> QueryNode (for "query")
# - an edge from IntentClassificationNode -> MutationNode (for "mutation")

# For demonstration, let's do it in a simpler if/else structure:


def main():
    print("Welcome to the Finance Assistant! Type 'exit' to quit.\n")

    classifier = IntentClassificationNode()
    query_node = QueryNode()
    mutation_node = MutationNode()

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break

        intent = classifier.run(user_input)
        if intent == "query":
            query_node.run(user_input)
        else:
            mutation_node.run(user_input)


if __name__ == "__main__":
    main()
