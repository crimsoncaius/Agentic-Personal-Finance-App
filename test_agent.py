import unittest
from unittest.mock import patch, MagicMock
from agent import (
    classify_intent,
    generate_sql_with_llm,
    QueryNode,
    MutationNode,
    IntentClassificationNode,
)


class TestAgentPrompts(unittest.TestCase):
    def setUp(self):
        self.query_node = QueryNode()
        self.mutation_node = MutationNode()
        self.classifier = IntentClassificationNode()

    @patch("agent.client.chat.completions.create")
    def test_intent_classification(self, mock_create):
        # Test query intent
        mock_create.return_value.choices[0].message.content = "query"
        result = classify_intent("Show me my expenses")
        self.assertEqual(result, "query")

        # Test mutation intent
        mock_create.return_value.choices[0].message.content = "mutation"
        result = classify_intent("Add a new expense")
        self.assertEqual(result, "mutation")

        # Test fallback to query
        mock_create.return_value.choices[0].message.content = "invalid"
        result = classify_intent("Something unexpected")
        self.assertEqual(result, "query")

    @patch("agent.client.chat.completions.create")
    def test_query_node_prompts(self, mock_create):
        # Test expense query
        mock_create.return_value.choices[
            0
        ].message.content = """
        SELECT * FROM transactions 
        WHERE transaction_type = 'EXPENSE' 
        ORDER BY date DESC
        """
        with patch("agent.execute_sql_query") as mock_execute:
            mock_execute.return_value = [
                (1, 100.0, "2024-03-20", "Groceries", False, None, "EXPENSE", 1)
            ]
            self.query_node.run("Show me my recent expenses")

        # Test income query
        mock_create.return_value.choices[
            0
        ].message.content = """
        SELECT * FROM transactions 
        WHERE transaction_type = 'INCOME' 
        ORDER BY date DESC
        """
        with patch("agent.execute_sql_query") as mock_execute:
            mock_execute.return_value = [
                (2, 5000.0, "2024-03-15", "Salary", True, "monthly", "INCOME", 2)
            ]
            self.query_node.run("Show me my income")

    @patch("agent.client.chat.completions.create")
    def test_mutation_node_prompts(self, mock_create):
        # Test adding expense
        mock_create.return_value.choices[
            0
        ].message.content = """
        INSERT INTO transactions (amount, date, description, transaction_type, category_id)
        VALUES (50.0, '2024-03-20', 'Dinner', 'EXPENSE', 1)
        """
        with patch("agent.execute_sql_query") as mock_execute:
            mock_execute.return_value = 1
            self.mutation_node.run("Add a dinner expense of $50")

        # Test adding income
        mock_create.return_value.choices[
            0
        ].message.content = """
        INSERT INTO transactions (amount, date, description, is_recurring, recurrence_period, transaction_type, category_id)
        VALUES (5000.0, '2024-03-15', 'Monthly Salary', true, 'monthly', 'INCOME', 2)
        """
        with patch("agent.execute_sql_query") as mock_execute:
            mock_execute.return_value = 1
            self.mutation_node.run("Add my monthly salary of $5000")

    def test_common_user_queries(self):
        """Test common user queries that should be handled correctly"""
        common_queries = [
            # Basic queries
            "What are my total expenses this month?",
            "Show me my income for the last 3 months",
            "Which categories am I spending the most on?",
            "What's my monthly recurring income?",
            # Basic mutations
            "Add a new expense of $25 for groceries",
            "Record my monthly rent payment of $1500",
            "Add a new income category called 'Freelance'",
            "Update my salary to $6000 per month",
            # Complex queries with calculations
            "Show me my net income after all expenses",
            # Time-based queries with various formats
            "Show expenses from January to March",
            "What did I spend last week?",
            "Display my income for Q1 2024",
            "Show me transactions from the beginning of the year",
            # Category-specific queries
            "How much did I spend on food this month?",
            "Show me all transactions in the 'Entertainment' category",
            "What's my total income from freelance work?",
            "List all expenses except groceries",
            # Recurring transaction queries
            "Show me all my recurring payments",
            "What subscriptions do I have?",
            "List my monthly recurring expenses",
            "Show me non-recurring transactions",
            # Edge cases and ambiguous queries
            "What's my balance?",  # Ambiguous - could be checking or savings
            "Show me my money",  # Very vague
            "How am I doing?",  # Ambiguous financial status request
            "What's my budget?",  # Could be viewing or setting
            # Complex financial analysis
            "Compare my spending this month to last month",
            "Show me my top 3 expense categories",
            "What's my average daily spending?",
            "Calculate my monthly savings trend",
            # Multi-part queries
            "Show me my expenses and income for March",
            "List my recurring payments and one-time expenses",
            "What's my income vs expenses this quarter?",
            "Show me my budget and actual spending",
            # Negative and zero amounts
            "Add a refund of -$50 for returned items",
            "Record a $0 transaction for free items",
            "Show me transactions with zero amount",
            "List all negative transactions",
            # Date edge cases
            "Show transactions from today",
            "What did I spend on my birthday?",
            "Show me expenses from the last day of each month",
            "List transactions from the first week of 2024",
            # Category management
            "Rename 'Food' category to 'Groceries'",
            "Delete the 'Entertainment' category",
            "Merge 'Food' and 'Dining' categories",
            "Split 'Shopping' into 'Clothes' and 'Electronics'",
            # Complex financial goals
            "Am I on track to save $1000 this month?",
            "Show me my progress towards my savings goal",
            "Calculate if I can afford a $5000 vacation",
            "What's my projected savings for the year?",
            # Error-prone queries
            "Show me transactions from invalid date",
            "Add expense with negative category",
            "Update transaction with invalid amount",
            "Delete non-existent category",
        ]

        for query in common_queries:
            intent = self.classifier.run(query)
            self.assertIn(
                intent,
                ["query", "mutation"],
                f"Query '{query}' resulted in invalid intent: {intent}",
            )

            # Additional validation for specific query types
            if "calculate" in query.lower() or "show" in query.lower():
                self.assertEqual(
                    intent,
                    "query",
                    f"Calculation/display query '{query}' should be a query",
                )
            if any(
                word in query.lower()
                for word in ["add", "update", "delete", "rename", "merge", "split"]
            ):
                self.assertEqual(
                    intent,
                    "mutation",
                    f"Modification query '{query}' should be a mutation",
                )

    @patch("agent.client.chat.completions.create")
    def test_sql_generation(self, mock_create):
        # Test complex query generation
        mock_create.return_value.choices[
            0
        ].message.content = """
        SELECT 
            c.name as category,
            SUM(t.amount) as total_amount,
            COUNT(*) as transaction_count
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.transaction_type = 'EXPENSE'
        GROUP BY c.name
        ORDER BY total_amount DESC
        """
        sql = generate_sql_with_llm("", "Show me spending by category")
        self.assertIn("SELECT", sql)
        self.assertIn("JOIN", sql)
        self.assertIn("GROUP BY", sql)


if __name__ == "__main__":
    unittest.main()
