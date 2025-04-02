import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def extract_amount(text: str) -> float:
    """Extract amount from text containing currency."""
    # Look for patterns like $100, $100.50, 100 dollars, etc.
    amount_match = re.search(r"\$?(\d+(?:\.\d{2})?)\s*(?:dollars?)?", text)
    if amount_match:
        return float(amount_match.group(1))
    return 0.0


def extract_date(text: str) -> str:
    """Extract date from text or return today's date."""
    # Look for "today", "yesterday", "tomorrow", or specific dates
    text = text.lower()
    today = datetime.now()

    if "today" in text:
        return today.strftime("%Y-%m-%d")
    elif "yesterday" in text:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "tomorrow" in text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    # Try to find a date pattern (can be expanded based on common formats)
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if date_match:
        return date_match.group(0)

    return today.strftime("%Y-%m-%d")


def generate_sql_with_llm(system_prompt: str, user_input: str) -> dict:
    """
    Generate SQL based on the system prompt and user input.
    Returns a dictionary containing the SQL query and extracted parameters.
    """
    try:
        user_input = user_input.lower().strip()
        result = {
            "sql": "",
            "params": {},
            "operation": "",
            "success": True,
            "error": None,
        }

        # Show recent transactions
        if re.search(
            r"(show|view|list|get|display).*(entries|transactions).*last\s+week",
            user_input,
        ):
            result[
                "sql"
            ] = """
                SELECT t.id, t.amount, t.date, t.description, t.is_recurring, 
                       t.recurrence_period, t.transaction_type, c.name as category_name
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = :user_id 
                AND t.date >= date('now', '-7 days')
                ORDER BY t.date DESC, t.id DESC
            """
            result["operation"] = "select"
            return result

        # View/Show categories
        if re.search(
            r"(show|view|list|get|display).*(categories|category)", user_input
        ):
            result["sql"] = (
                "SELECT name, transaction_type FROM categories WHERE user_id = :user_id ORDER BY name"
            )
            result["operation"] = "select"
            return result

        # Create/Add category
        match = re.search(
            r'(create|add|new|make).+category.+called.+["\'](.+)["\'].*(?:for|as).*(expense|income)',
            user_input,
        )
        if match:
            category_name = match.group(2)
            transaction_type = match.group(3).upper()
            result["sql"] = (
                "INSERT INTO categories (name, transaction_type, user_id) VALUES (:name, :type, :user_id)"
            )
            result["params"].update({"name": category_name, "type": transaction_type})
            result["operation"] = "insert"
            return result

        # Add transaction (e.g., "Add curry chicken today $100")
        match = re.search(
            r"(add|create|new|record|log)\s+(.+?)(?:\s+on\s+|\s+for\s+|\s+)(?:(\$\d+(?:\.\d{2})?)|(\d+(?:\.\d{2})?)\s*dollars?)",
            user_input,
        )
        if match:
            description = match.group(2).strip()
            amount = extract_amount(user_input)
            date_str = extract_date(user_input)

            # Default to EXPENSE type, can be enhanced to detect INCOME based on context
            transaction_type = "EXPENSE"

            result[
                "sql"
            ] = """
                INSERT INTO transactions 
                (amount, date, description, transaction_type, category_id, user_id, is_recurring) 
                VALUES 
                (:amount, :date, :description, :type, 
                 (SELECT id FROM categories WHERE name = 'Other' AND transaction_type = :type AND user_id = :user_id LIMIT 1),
                 :user_id, false)
            """
            result["params"].update(
                {
                    "amount": amount,
                    "date": date_str,
                    "description": description,
                    "type": transaction_type,
                }
            )
            result["operation"] = "insert"
            return result

        # Update/Change category
        match = re.search(
            r'(update|change|rename|modify).+category.+["\'](.+)["\'].+to.+["\'](.+)["\']',
            user_input,
        )
        if match:
            old_name = match.group(2)
            new_name = match.group(3)
            result["sql"] = (
                "UPDATE categories SET name = :new_name WHERE name = :old_name AND user_id = :user_id"
            )
            result["params"].update({"old_name": old_name, "new_name": new_name})
            result["operation"] = "update"
            return result

        # Delete/Remove category
        match = re.search(r'(delete|remove|drop).+category.+["\'](.+)["\']', user_input)
        if match:
            category_name = match.group(2)
            result["sql"] = (
                "DELETE FROM categories WHERE name = :name AND user_id = :user_id"
            )
            result["params"].update({"name": category_name})
            result["operation"] = "delete"
            return result

        logger.warning(f"Could not generate SQL for input: {user_input}")
        result["success"] = False
        result["error"] = "Could not understand the command"
        return result

    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        return {
            "sql": "",
            "params": {},
            "operation": "",
            "success": False,
            "error": str(e),
        }
