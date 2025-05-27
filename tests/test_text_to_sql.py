"""
Test suite for Text-to-SQL functionality
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.sql_agent import (
    DatabaseIntrospector,
    SQLAgent,
    SQLSecurityValidator,
)
from agents.text_to_sql_demo import TextToSQLDemo


class TestSQLSecurityValidator(unittest.TestCase):
    """Test the SQL security validator."""

    def setUp(self):
        self.validator = SQLSecurityValidator()

    def test_valid_select_query(self):
        """Test that valid SELECT queries pass validation."""
        valid_queries = [
            "SELECT * FROM customers",
            "SELECT name, email FROM customers WHERE state = 'CA'",
            "SELECT COUNT(*) FROM orders",
            "SELECT c.name, o.total FROM customers c JOIN orders o ON c.id = o.customer_id",
        ]

        for query in valid_queries:
            is_valid, error = self.validator.validate_query(query)
            self.assertTrue(is_valid, f"Query should be valid: {query}")
            self.assertIsNone(error)

    def test_dangerous_queries_blocked(self):
        """Test that dangerous queries are blocked."""
        dangerous_queries = [
            "DROP TABLE customers",
            "DELETE FROM orders",
            "UPDATE products SET price = 0",
            "INSERT INTO customers VALUES (1, 'test')",
            "ALTER TABLE products ADD COLUMN test TEXT",
            "TRUNCATE TABLE orders",
            "GRANT ALL ON customers TO public",
            "REVOKE ALL ON customers FROM user",
        ]

        for query in dangerous_queries:
            is_valid, error = self.validator.validate_query(query)
            self.assertFalse(is_valid, f"Query should be blocked: {query}")
            self.assertIsNotNone(error)

    def test_complex_queries_with_limits(self):
        """Test that overly complex queries are blocked."""
        # Query with too many parentheses
        complex_query = "SELECT * FROM customers " + "(".join([""] * 12) + ")"
        is_valid, error = self.validator.validate_query(complex_query)
        self.assertFalse(is_valid)

        # Query that's too long
        long_query = "SELECT * FROM customers WHERE " + " AND ".join(
            [f"id = {i}" for i in range(100)]
        )
        is_valid, error = self.validator.validate_query(long_query)
        self.assertFalse(is_valid)

    def test_sql_injection_patterns(self):
        """Test that SQL injection patterns are blocked."""
        injection_queries = [
            "SELECT * FROM customers; DROP TABLE orders;",
            "SELECT * FROM customers -- comment",
            "SELECT * FROM customers /* comment */",
            "SELECT * FROM customers WHERE id = 1 OR '1'='1'",
        ]

        for query in injection_queries:
            is_valid, error = self.validator.validate_query(query)
            self.assertFalse(is_valid, f"Injection query should be blocked: {query}")


class TestDatabaseIntrospector(unittest.TestCase):
    """Test the database introspector."""

    def setUp(self):
        # Mock connection parameters
        self.mock_params = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass",
        }
        self.introspector = DatabaseIntrospector(self.mock_params)

    @patch("agents.sql_agent.psycopg2.connect")
    def test_schema_extraction(self, mock_connect):
        """Test schema information extraction."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock table list query
        mock_cursor.fetchall.side_effect = [
            [("customers",), ("orders",)],  # Tables
            # Customers table columns
            [
                ("customer_id", "integer", "NO", None, None),
                ("first_name", "character varying", "NO", None, 50),
                ("email", "character varying", "NO", None, 100),
            ],
            [],  # No foreign keys for customers
            # Orders table columns
            [
                ("order_id", "integer", "NO", None, None),
                ("customer_id", "integer", "NO", None, None),
                ("total_amount", "numeric", "NO", None, None),
            ],
            [("customer_id", "customers", "customer_id")],  # Foreign key for orders
        ]

        schema_info = self.introspector.get_schema_info("test_schema")

        # Verify schema structure
        self.assertEqual(len(schema_info), 2)
        self.assertIn("customers", schema_info)
        self.assertIn("orders", schema_info)

        # Verify customers table
        customers_table = schema_info["customers"]
        self.assertEqual(customers_table.name, "customers")
        self.assertEqual(len(customers_table.columns), 3)
        self.assertEqual(len(customers_table.foreign_keys), 0)

        # Verify orders table
        orders_table = schema_info["orders"]
        self.assertEqual(orders_table.name, "orders")
        self.assertEqual(len(orders_table.columns), 3)
        self.assertEqual(len(orders_table.foreign_keys), 1)


class TestSQLAgent(unittest.TestCase):
    """Test the main SQL Agent class."""

    def setUp(self):
        self.mock_db_params = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass",
        }

    @patch("agents.sql_agent.DatabaseIntrospector")
    @patch("agents.sql_agent.BedrockNL2SQL")
    @patch("agents.sql_agent.SQLSecurityValidator")
    def test_agent_initialization(self, mock_validator, mock_nl2sql, mock_introspector):
        """Test SQL agent initialization."""
        agent = SQLAgent(self.mock_db_params)

        # Verify components are initialized
        self.assertIsNotNone(agent.introspector)
        self.assertIsNotNone(agent.nl2sql)
        self.assertIsNotNone(agent.validator)
        self.assertIsNone(agent.schema_cache)

    @patch("agents.sql_agent.psycopg2.connect")
    def test_query_execution_success(self, mock_connect):
        """Test successful query execution."""
        # Mock database components
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock query results
        mock_cursor.description = [("count",), ("name",)]
        mock_cursor.fetchall.return_value = [(10, "test")]

        # Create agent with mocked components
        with (
            patch("agents.sql_agent.DatabaseIntrospector"),
            patch("agents.sql_agent.BedrockNL2SQL") as mock_nl2sql,
            patch("agents.sql_agent.SQLSecurityValidator") as mock_validator,
        ):

            agent = SQLAgent(self.mock_db_params)

            # Mock the validation and SQL generation
            mock_validator.return_value.validate_query.return_value = (True, None)
            mock_nl2sql.return_value.generate_sql.return_value = "SELECT COUNT(*) FROM customers"

            # Mock schema cache
            agent.schema_cache = {"customers": Mock()}

            # Execute query
            result = agent._execute_query("SELECT COUNT(*) FROM customers")

            # Verify result
            self.assertTrue(result.success)
            self.assertIsNotNone(result.data)
            self.assertEqual(len(result.data), 1)
            self.assertEqual(result.data[0]["count"], 10)

    @patch("agents.sql_agent.psycopg2.connect")
    def test_query_execution_failure(self, mock_connect):
        """Test query execution failure handling."""
        # Mock database error
        mock_connect.side_effect = Exception("Database connection failed")

        with (
            patch("agents.sql_agent.DatabaseIntrospector"),
            patch("agents.sql_agent.BedrockNL2SQL"),
            patch("agents.sql_agent.SQLSecurityValidator"),
        ):

            agent = SQLAgent(self.mock_db_params)
            result = agent._execute_query("SELECT * FROM customers")

            # Verify error handling
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error)
            self.assertIn("Database connection failed", result.error)


class TestTextToSQLDemo(unittest.TestCase):
    """Test the Text-to-SQL demo class."""

    def setUp(self):
        self.mock_db_params = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass",
        }
        self.demo = TextToSQLDemo(self.mock_db_params)

    def test_demo_initialization(self):
        """Test demo class initialization."""
        self.assertEqual(self.demo.db_params, self.mock_db_params)
        self.assertIsNone(self.demo.sql_agent)
        self.assertEqual(self.demo.demo_results, [])

    def test_sql_formatting(self):
        """Test SQL formatting functionality."""
        sql = "SELECT * FROM customers WHERE state = 'CA' ORDER BY name"
        formatted = self.demo._format_sql(sql)

        # Should have line breaks after keywords
        self.assertIn("\nFROM", formatted)
        self.assertIn("\nWHERE", formatted)
        self.assertIn("\nORDER BY", formatted)

    def test_row_formatting(self):
        """Test database row formatting."""
        row = {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "long_description": "This is a very long description that should be truncated",
        }

        formatted = self.demo._format_row(row)

        # Should contain all fields
        self.assertIn("id: 1", formatted)
        self.assertIn("name: John Doe", formatted)
        self.assertIn("email: john.doe@example.com", formatted)

        # Long text should be truncated
        self.assertIn("long_description: This is a very long descri...", formatted)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete Text-to-SQL system."""

    def test_end_to_end_flow(self):
        """Test the complete flow from natural language to SQL results."""
        # This would be a more comprehensive test with actual database
        # For now, just test that components can be initialized together

        mock_db_params = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass",
        }

        with patch("agents.sql_agent.psycopg2.connect"), patch("agents.sql_agent.boto3.client"):

            try:
                agent = SQLAgent(mock_db_params)
                demo = TextToSQLDemo(mock_db_params)

                # If we get here without exceptions, basic integration works
                self.assertTrue(True)

            except Exception as e:
                self.fail(f"Integration test failed: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
