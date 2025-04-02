from typing import Dict, Any
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from ..schemas import ChatResponse
from .sql_generator import generate_sql_with_llm
from .sql_executor import execute_sql_query

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generates human-readable responses for different operations."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def format_transaction_data(self, rows) -> str:
        """Format transaction data into a readable string."""
        if not rows:
            return "No transactions found for the specified period."

        # Group transactions by date
        transactions_by_date = {}
        total_expense = 0
        total_income = 0

        for row in rows:
            # Convert row to dict for easier access
            row_dict = {
                "id": row[0],
                "amount": row[1],
                "date": row[2],
                "description": row[3],
                "is_recurring": row[4],
                "recurrence_period": row[5],
                "transaction_type": row[6],
                "category_name": row[7],
            }

            date_str = row_dict["date"]
            if date_str not in transactions_by_date:
                transactions_by_date[date_str] = []
            transactions_by_date[date_str].append(row_dict)

            # Update totals
            amount = float(row_dict["amount"])
            if row_dict["transaction_type"] == "EXPENSE":
                total_expense += amount
            else:
                total_income += amount

        # Format the output
        output = []
        for date_str in sorted(transactions_by_date.keys(), reverse=True):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            output.append(f"\n📅 {formatted_date}")

            for row_dict in sorted(
                transactions_by_date[date_str], key=lambda x: x["transaction_type"]
            ):
                symbol = "💰" if row_dict["transaction_type"] == "INCOME" else "💳"
                amount_str = f"${row_dict['amount']:,.2f}"
                description = row_dict["description"]
                if row_dict["is_recurring"]:
                    description = f"{description} (🔄 {row_dict['recurrence_period']})"
                category_str = (
                    f"[{row_dict['category_name']}]"
                    if row_dict["category_name"]
                    else "[Uncategorized]"
                )

                output.append(
                    f"{symbol} {amount_str:>10} - {description} {category_str}"
                )

        # Add summary
        output.append("\n📊 Summary:")
        output.append(f"💰 Total Income:  ${total_income:,.2f}")
        output.append(f"💳 Total Expense: ${total_expense:,.2f}")
        output.append(f"📈 Net Change:    ${total_income - total_expense:,.2f}")

        return "\n".join(output)

    def generate_response(self, user_input: str) -> ChatResponse:
        """Generate a response to a user's chat message."""
        try:
            # Generate SQL query
            query_info = generate_sql_with_llm("", user_input)

            if not query_info["success"]:
                return ChatResponse(
                    response="I'm not sure how to help with that request. Could you please rephrase it?",
                    success=False,
                    error=query_info["error"],
                )

            # Execute the query
            result = execute_sql_query(query_info, self.user_id)

            if not result["success"]:
                return ChatResponse(
                    response=f"I encountered an error while processing your request: {result['error']}",
                    success=False,
                    error=result["error"],
                )

            # Generate appropriate response based on the operation and result
            operation = result["operation"]
            if operation == "select":
                if (
                    "transactions" in user_input.lower()
                    or "entries" in user_input.lower()
                ):
                    formatted_data = self.format_transaction_data(result["data"])

                    # Convert rows to list of dicts for JSON serialization
                    data_dicts = []
                    if result["data"]:
                        for row in result["data"]:
                            data_dicts.append(
                                {
                                    "id": row[0],
                                    "amount": row[1],
                                    "date": row[2],
                                    "description": row[3],
                                    "is_recurring": row[4],
                                    "recurrence_period": row[5],
                                    "transaction_type": row[6],
                                    "category_name": row[7],
                                }
                            )

                    return ChatResponse(
                        response=formatted_data,
                        success=True,
                        data={"transactions": data_dicts},  # Wrap in dict for Pydantic
                    )
                else:
                    # Convert other types of results to dicts too
                    data_dicts = []
                    if result["data"]:
                        for row in result["data"]:
                            data_dicts.append(dict(zip(["name", "type"], row)))

                    return ChatResponse(
                        response="Here are the items you requested.",
                        success=True,
                        data={"items": data_dicts},  # Wrap in dict for Pydantic
                    )
            elif operation == "insert":
                if "category" in user_input.lower():
                    return ChatResponse(
                        response="I've added the new category for you.", success=True
                    )
                else:
                    amount = query_info["params"].get("amount", 0)
                    description = query_info["params"].get("description", "")
                    date_str = query_info["params"].get("date", "")
                    return ChatResponse(
                        response=f"I've added the transaction for {description} on {date_str} for ${amount:.2f}.",
                        success=True,
                    )
            elif operation == "update":
                return ChatResponse(
                    response="I've updated the item as requested.", success=True
                )
            elif operation == "delete":
                return ChatResponse(
                    response="I've deleted the item as requested.", success=True
                )
            else:
                return ChatResponse(
                    response="I've processed your request successfully.", success=True
                )

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ChatResponse(
                response="I encountered an error processing your request. Please try again.",
                success=False,
                error=str(e),
            )

    @staticmethod
    def generate_operation_response(operation_type: str, details: Dict) -> str:
        """Generate a response based on the operation type and details."""
        try:
            operation_type = operation_type.lower()

            if operation_type == "select":
                return "Here are the items you requested."

            elif operation_type == "insert":
                if "category" in details.get("user_input", "").lower():
                    return "I've added the new category for you."
                else:
                    return "I've added the new item for you."

            elif operation_type == "update":
                if "category" in details.get("user_input", "").lower():
                    return "I've updated the category as requested."
                else:
                    return "I've updated the item as requested."

            elif operation_type == "delete":
                if "category" in details.get("user_input", "").lower():
                    return "I've deleted the category for you."
                else:
                    return "I've deleted the item as requested."

            else:
                logger.warning(f"Unknown operation type: {operation_type}")
                return "I've processed your request."

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I've processed your request, but couldn't generate a specific response."
