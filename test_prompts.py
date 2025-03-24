import unittest
from unittest.mock import patch
from agent import (
    classify_intent,
    generate_sql_with_llm,
    QueryNode,
    MutationNode,
    IntentClassificationNode,
)
import os
from datetime import datetime


class TestPrompts(unittest.TestCase):
    def setUp(self):
        self.query_node = QueryNode()
        self.mutation_node = MutationNode()
        self.classifier = IntentClassificationNode()
        # Create output directory if it doesn't exist
        self.output_dir = "test_output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Create output file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = os.path.join(
            self.output_dir, f"prompt_sql_mapping_{timestamp}.txt"
        )

    def write_to_file(self, prompt, sql, intent):
        """Write prompt, SQL, and intent to the output file"""
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Prompt: {prompt}\n")
            f.write(f"Intent: {intent}\n")
            f.write(f"SQL: {sql}\n")
            f.write(f"{'='*80}\n")

    def get_mock_sql(self, prompt):
        """Generate realistic mock SQL based on the prompt"""
        prompt_lower = prompt.lower()

        # Basic transaction queries
        if "show me all expenses" in prompt_lower:
            return "SELECT * FROM transactions WHERE transaction_type = 'EXPENSE' ORDER BY date DESC"
        elif "total income" in prompt_lower:
            return "SELECT SUM(amount) as total_income FROM transactions WHERE transaction_type = 'INCOME'"
        elif "recent transactions" in prompt_lower:
            return "SELECT * FROM transactions ORDER BY date DESC LIMIT 10"
        elif "transactions from last week" in prompt_lower:
            return "SELECT * FROM transactions WHERE date >= date('now', '-7 days') ORDER BY date DESC"

        # Category queries
        elif "show me all categories" in prompt_lower:
            return "SELECT * FROM categories ORDER BY name"
        elif "expense categories" in prompt_lower:
            return "SELECT * FROM categories WHERE transaction_type = 'EXPENSE' ORDER BY name"
        elif "income categories" in prompt_lower:
            return "SELECT * FROM categories WHERE transaction_type = 'INCOME' ORDER BY name"

        # Transaction mutations
        elif "add an expense" in prompt_lower:
            return "INSERT INTO transactions (amount, date, description, transaction_type, category_id) VALUES (50.0, date('now'), 'Groceries', 'EXPENSE', 1)"
        elif "record my salary" in prompt_lower:
            return "INSERT INTO transactions (amount, date, description, is_recurring, recurrence_period, transaction_type, category_id) VALUES (5000.0, date('now'), 'Monthly Salary', true, 'monthly', 'INCOME', 2)"
        elif "add a new expense category" in prompt_lower:
            return "INSERT INTO categories (name, transaction_type) VALUES ('Transportation', 'EXPENSE')"
        elif "add a new income category" in prompt_lower:
            return "INSERT INTO categories (name, transaction_type) VALUES ('Freelance', 'INCOME')"

        # Time-based queries
        elif "from january to march" in prompt_lower:
            return "SELECT * FROM transactions WHERE date BETWEEN '2024-01-01' AND '2024-03-31' ORDER BY date"
        elif "last month" in prompt_lower:
            return "SELECT * FROM transactions WHERE date >= date('now', 'start of month', '-1 month') AND date < date('now', 'start of month')"
        elif "q1 2024" in prompt_lower:
            return "SELECT * FROM transactions WHERE date BETWEEN '2024-01-01' AND '2024-03-31' ORDER BY date"

        # Category-specific queries
        elif "spend on food" in prompt_lower:
            return "SELECT * FROM transactions t JOIN categories c ON t.category_id = c.id WHERE c.name = 'Food' AND t.transaction_type = 'EXPENSE'"
        elif "entertainment category" in prompt_lower:
            return "SELECT * FROM transactions t JOIN categories c ON t.category_id = c.id WHERE c.name = 'Entertainment'"

        # Recurring transaction queries
        elif "recurring payments" in prompt_lower:
            return "SELECT * FROM transactions WHERE is_recurring = true ORDER BY date"
        elif "subscriptions" in prompt_lower:
            return "SELECT * FROM transactions WHERE is_recurring = true AND recurrence_period IN ('monthly', 'yearly')"

        # Category management
        elif "rename" in prompt_lower:
            return "UPDATE categories SET name = 'Groceries' WHERE name = 'Food'"
        elif "delete" in prompt_lower and "category" in prompt_lower:
            return "DELETE FROM categories WHERE name = 'Entertainment'"
        elif "merge" in prompt_lower:
            return "UPDATE transactions SET category_id = (SELECT id FROM categories WHERE name = 'Food') WHERE category_id IN (SELECT id FROM categories WHERE name IN ('Food', 'Dining'))"

        # Complex queries
        elif "spending by category" in prompt_lower:
            return "SELECT c.name as category, SUM(t.amount) as total_amount FROM transactions t JOIN categories c ON t.category_id = c.id WHERE t.transaction_type = 'EXPENSE' GROUP BY c.name ORDER BY total_amount DESC"
        elif "net income" in prompt_lower:
            return "SELECT (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE transaction_type = 'INCOME') - (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE transaction_type = 'EXPENSE') as net_income"

        # Default case
        return "SELECT * FROM transactions ORDER BY date DESC"

    @patch("agent.client.chat.completions.create")
    def test_basic_prompts(self, mock_create):
        """Test basic transaction and category prompts"""
        basic_prompts = [
            # Transaction queries
            "Show me all my expenses",
            "What's my total income this month?",
            "List my recent transactions",
            "Show me transactions from last week",
            # Category queries
            "Show me all categories",
            "What categories do I have?",
            "List my expense categories",
            "Show me my income categories",
            # Transaction mutations
            "Add an expense of $50 for groceries",
            "Record my salary of $5000",
            "Add a new expense category called 'Transportation'",
            "Add a new income category called 'Freelance'",
        ]

        for prompt in basic_prompts:
            intent = self.classifier.run(prompt)
            mock_create.return_value.choices[0].message.content = (
                "SELECT * FROM transactions"
            )
            sql = generate_sql_with_llm("", prompt)
            self.assertIn(
                intent,
                ["query", "mutation"],
                f"Prompt '{prompt}' resulted in invalid intent: {intent}",
            )
            self.write_to_file(prompt, sql, intent)

    @patch("agent.client.chat.completions.create")
    def test_complex_transaction_prompts(self, mock_create):
        """Test complex transaction-related prompts"""
        complex_prompts = [
            # Time-based queries
            "Show me expenses from January to March",
            "What did I spend last month?",
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
        ]

        for prompt in complex_prompts:
            intent = self.classifier.run(prompt)
            mock_create.return_value.choices[0].message.content = (
                "SELECT * FROM transactions"
            )
            sql = generate_sql_with_llm("", prompt)
            self.assertIn(
                intent,
                ["query", "mutation"],
                f"Prompt '{prompt}' resulted in invalid intent: {intent}",
            )
            self.write_to_file(prompt, sql, intent)

    @patch("agent.client.chat.completions.create")
    def test_edge_case_prompts(self, mock_create):
        """Test edge cases and ambiguous prompts"""
        edge_cases = [
            # Ambiguous queries
            "What's my balance?",
            "Show me my money",
            "How am I doing?",
            # Complex calculations
            "What's my net income after expenses?",
            "Show me my average daily spending",
            "Calculate my total expenses this month",
            # Multi-part queries
            "Show me my expenses and income for March",
            "List my recurring payments and one-time expenses",
            "What's my income vs expenses this quarter?",
            # Special cases
            "Add a refund of -$50 for returned items",
            "Record a $0 transaction for free items",
            "Show me transactions with zero amount",
            "List all negative transactions",
        ]

        for prompt in edge_cases:
            intent = self.classifier.run(prompt)
            mock_create.return_value.choices[0].message.content = (
                "SELECT * FROM transactions"
            )
            sql = generate_sql_with_llm("", prompt)
            self.assertIn(
                intent,
                ["query", "mutation"],
                f"Prompt '{prompt}' resulted in invalid intent: {intent}",
            )
            self.write_to_file(prompt, sql, intent)

    @patch("agent.client.chat.completions.create")
    def test_category_management_prompts(self, mock_create):
        """Test category management prompts"""
        category_prompts = [
            # Category modifications
            "Rename 'Food' category to 'Groceries'",
            "Delete the 'Entertainment' category",
            "Merge 'Food' and 'Dining' categories",
            "Split 'Shopping' into 'Clothes' and 'Electronics'",
            # Category queries
            "Show me all categories and their transaction types",
            "List categories with no transactions",
            "Show me categories with the most transactions",
            "What categories have recurring transactions?",
        ]

        for prompt in category_prompts:
            intent = self.classifier.run(prompt)
            mock_create.return_value.choices[0].message.content = (
                "SELECT * FROM transactions"
            )
            sql = generate_sql_with_llm("", prompt)
            self.assertIn(
                intent,
                ["query", "mutation"],
                f"Prompt '{prompt}' resulted in invalid intent: {intent}",
            )
            self.write_to_file(prompt, sql, intent)

    @patch("agent.client.chat.completions.create")
    def test_sql_generation_prompts(self, mock_create):
        """Test SQL generation for various prompts"""
        sql_prompts = [
            # Basic queries
            "Show me all expenses",
            "List my income categories",
            # Complex queries
            "Show me spending by category",
            "What's my total income this month?",
            # Category queries
            "Show me transactions in the Food category",
            "List all categories and their transaction counts",
        ]

        for prompt in sql_prompts:
            # Set up the mock to return a proper SQL string
            mock_create.return_value.choices[0].message.content = (
                "SELECT * FROM transactions"
            )
            sql = generate_sql_with_llm("", prompt)
            intent = self.classifier.run(prompt)
            self.assertIsInstance(sql, str)
            self.assertIn("SELECT", sql)
            self.write_to_file(prompt, sql, intent)

    @patch("agent.client.chat.completions.create")
    def test_error_handling_prompts(self, mock_create):
        """Test prompts that should be handled gracefully"""
        error_prompts = [
            # Invalid dates
            "Show me transactions from invalid date",
            # Invalid categories
            "Add expense with negative category",
            # Invalid amounts
            "Update transaction with invalid amount",
            # Non-existent items
            "Delete non-existent category",
            # Malformed queries
            "Show me...",
            "Add...",
            "What...",
            "List...",
        ]

        for prompt in error_prompts:
            intent = self.classifier.run(prompt)
            mock_create.return_value.choices[0].message.content = (
                "SELECT * FROM transactions"
            )
            sql = generate_sql_with_llm("", prompt)
            self.assertIn(
                intent,
                ["query", "mutation"],
                f"Error prompt '{prompt}' should still result in valid intent",
            )
            self.write_to_file(prompt, sql, intent)

    @patch("agent.client.chat.completions.create")
    def test_complete_workflow(self, mock_create):
        """Test the complete workflow from intent classification to node execution"""
        test_cases = [
            # Query cases
            {
                "prompt": "Show me all expenses",
                "intent": "query",
                "expected_sql": "SELECT * FROM transactions WHERE transaction_type = 'EXPENSE' ORDER BY date DESC",
            },
            {
                "prompt": "What's my total income?",
                "intent": "query",
                "expected_sql": "SELECT SUM(amount) as total_income FROM transactions WHERE transaction_type = 'INCOME'",
            },
            # Mutation cases
            {
                "prompt": "Add an expense of $50 for groceries",
                "intent": "mutation",
                "expected_sql": "INSERT INTO transactions (amount, date, description, transaction_type, category_id) VALUES (50.0, date('now'), 'Groceries', 'EXPENSE', 1)",
            },
            {
                "prompt": "Add a new category called 'Transportation'",
                "intent": "mutation",
                "expected_sql": "INSERT INTO categories (name, transaction_type) VALUES ('Transportation', 'EXPENSE')",
            },
        ]

        for case in test_cases:
            # First, mock the intent classification
            mock_create.return_value.choices[0].message.content = case["intent"]
            intent = self.classifier.run(case["prompt"])

            # Verify intent classification
            self.assertEqual(
                intent,
                case["intent"],
                f"Intent classification failed for prompt: {case['prompt']}",
            )

            # Then, mock the SQL generation
            mock_create.return_value.choices[0].message.content = case["expected_sql"]

            # Execute the appropriate node based on intent
            if intent == "query":
                self.query_node.run(case["prompt"])
            else:
                self.mutation_node.run(case["prompt"])

            # Write test case to file
            self.write_to_file(case["prompt"], case["expected_sql"], intent)

    def tearDown(self):
        """Clean up after tests"""
        # Add a summary at the end of the file
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write("Test Summary\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n")


if __name__ == "__main__":
    unittest.main()
