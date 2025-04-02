from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Handles storing and managing conversation history for users."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.messages: List[Dict] = []
        self.transactions: List[Dict] = []
        self.last_interaction: Optional[datetime] = None

    def add_interaction(self, user_input: str, assistant_response: str) -> None:
        """Add a user-assistant interaction to the conversation history."""
        try:
            interaction = {
                "timestamp": datetime.now(),
                "user_input": user_input,
                "assistant_response": assistant_response,
            }
            self.messages.append(interaction)
            self.last_interaction = interaction["timestamp"]
            logger.debug(f"Added interaction for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error adding interaction for user {self.user_id}: {e}")

    def add_transaction(
        self, operation_type: str, sql_query: str, details: Dict
    ) -> None:
        """Add a transaction record to the conversation history."""
        try:
            transaction = {
                "timestamp": datetime.now(),
                "operation_type": operation_type,
                "sql_query": sql_query,
                "details": details,
            }
            self.transactions.append(transaction)
            logger.debug(f"Added transaction for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error adding transaction for user {self.user_id}: {e}")

    def get_recent_messages(self, limit: int = 5) -> List[Dict]:
        """Get the most recent messages from the conversation history."""
        try:
            return self.messages[-limit:]
        except Exception as e:
            logger.error(f"Error getting recent messages for user {self.user_id}: {e}")
            return []

    def get_recent_transactions(self, limit: int = 5) -> List[Dict]:
        """Get the most recent transactions from the conversation history."""
        try:
            return self.transactions[-limit:]
        except Exception as e:
            logger.error(
                f"Error getting recent transactions for user {self.user_id}: {e}"
            )
            return []

    def clear(self) -> None:
        """Clear all conversation history for the user."""
        try:
            self.messages = []
            self.transactions = []
            self.last_interaction = None
            logger.info(f"Cleared conversation history for user {self.user_id}")
        except Exception as e:
            logger.error(
                f"Error clearing conversation history for user {self.user_id}: {e}"
            )
            raise RuntimeError(f"Failed to clear conversation history: {e}")


# Global dictionary to store conversation memories for each user
conversation_memories: Dict[int, ConversationMemory] = {}
