"""
Text-to-SQL Demo Module

This module demonstrates the text-to-SQL capabilities using the workshop database.
It showcases natural language to SQL conversion with practical examples.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Any

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sql_agent import SQLAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextToSQLDemo:
    """Demonstration class for Text-to-SQL capabilities."""

    def __init__(self, db_params: dict[str, str], aws_endpoint: str | None = None):
        """Initialize the demo with database and AWS configuration."""
        self.db_params = db_params
        self.aws_endpoint = aws_endpoint
        self.sql_agent = None
        self.demo_results = []

    def initialize_agent(self) -> bool:
        """Initialize the SQL agent."""
        try:
            print("🔧 Initializing Text-to-SQL Agent...")
            self.sql_agent = SQLAgent(
                db_connection_params=self.db_params, aws_endpoint_url=self.aws_endpoint
            )

            # Refresh schema cache
            print("📊 Loading database schema...")
            self.sql_agent.refresh_schema("workshop")

            print("✅ SQL Agent initialized successfully!")
            print(f"📋 Cached schema for {len(self.sql_agent.schema_cache)} tables\n")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize SQL agent: {e}")
            return False

    def display_schema_overview(self):
        """Display a friendly overview of the database schema."""
        if not self.sql_agent:
            print("❌ SQL Agent not initialized")
            return

        print("=" * 60)
        print("🗄️  WORKSHOP DATABASE SCHEMA OVERVIEW")
        print("=" * 60)

        print(self.sql_agent.get_schema_summary())

        # Display sample data counts
        try:
            sample_queries = {
                "customers": "SELECT COUNT(*) FROM workshop.customers",
                "products": "SELECT COUNT(*) FROM workshop.products",
                "orders": "SELECT COUNT(*) FROM workshop.orders",
                "order_items": "SELECT COUNT(*) FROM workshop.order_items",
                "suppliers": "SELECT COUNT(*) FROM workshop.suppliers",
            }

            print("📈 Sample Data Counts:")
            for table, query in sample_queries.items():
                result = self.sql_agent._execute_query(query)
                if result.success and result.data:
                    count = result.data[0]["count"]
                    print(f"   {table:15}: {count:>6} records")
            print()

        except Exception as e:
            logger.error(f"Error getting data counts: {e}")

    def run_demo_queries(self):
        """Run a comprehensive set of demo queries."""
        if not self.sql_agent:
            print("❌ SQL Agent not initialized")
            return

        print("=" * 60)
        print("🔍 TEXT-TO-SQL DEMONSTRATION")
        print("=" * 60)

        # Categorized demo queries
        demo_categories = {
            "📊 Basic Queries": [
                "How many customers do we have?",
                "Show me all products in the Electronics category",
                "What customers are from California?",
            ],
            "📈 Aggregation & Analytics": [
                "What are the top 5 best-selling products?",
                "Who are our top 3 customers by total spending?",
                "What's the average order value?",
                "Show me total revenue by product category",
            ],
            "🔗 Join Queries": [
                "Show me customer names and their order counts",
                "Which products have never been ordered?",
                "List all orders with customer and product details",
            ],
            "📅 Time-Based Queries": [
                "Show me orders placed in November 2024",
                "What's our revenue for the last 30 days?",
                "Find customers who haven't ordered in the past month",
            ],
            "🎯 Advanced Analytics": [
                "Which customers have ordered from multiple categories?",
                "What's the profit margin for each product?",
                "Show me monthly sales trends",
                "Find suppliers with the most expensive products on average",
            ],
        }

        for category, queries in demo_categories.items():
            print(f"\n{category}")
            print("-" * 50)

            for i, query in enumerate(queries, 1):
                print(f"\n🔸 Query {i}: {query}")
                self._process_demo_query(query)

    def _process_demo_query(self, query: str):
        """Process a single demo query and display results."""
        start_time = datetime.now()

        try:
            result = self.sql_agent.query(query)
            execution_time = (datetime.now() - start_time).total_seconds()

            if result.success:
                print("   ✅ Generated SQL:")
                # Format SQL nicely
                formatted_sql = self._format_sql(result.query)
                for line in formatted_sql.split("\n"):
                    print(f"      {line}")

                if result.data:
                    print(f"   📊 Results: {len(result.data)} rows")
                    # Show first few results
                    for j, row in enumerate(result.data[:3]):
                        formatted_row = self._format_row(row)
                        print(f"      {j+1}. {formatted_row}")

                    if len(result.data) > 3:
                        print(f"      ... and {len(result.data) - 3} more rows")
                else:
                    print("   📊 No results returned")

                print(f"   ⏱️  Execution time: {execution_time:.3f}s")

                # Store result for summary
                self.demo_results.append(
                    {
                        "query": query,
                        "success": True,
                        "sql": result.query,
                        "result_count": len(result.data) if result.data else 0,
                        "execution_time": execution_time,
                    }
                )

            else:
                print(f"   ❌ Error: {result.error}")
                if result.query:
                    print(f"   Generated SQL: {result.query}")

                self.demo_results.append(
                    {
                        "query": query,
                        "success": False,
                        "error": result.error,
                        "execution_time": execution_time,
                    }
                )

        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            logger.error(f"Error processing query '{query}': {e}")

    def _format_sql(self, sql: str) -> str:
        """Format SQL query for better readability."""
        # Simple SQL formatting
        sql = sql.strip()

        # Add line breaks after common SQL keywords
        keywords = [
            "SELECT",
            "FROM",
            "WHERE",
            "GROUP BY",
            "ORDER BY",
            "HAVING",
            "JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
        ]
        for keyword in keywords:
            sql = sql.replace(f" {keyword} ", f"\n{keyword} ")

        return sql

    def _format_row(self, row: dict[str, Any]) -> str:
        """Format a database row for display."""
        formatted_items = []
        for key, value in row.items():
            if isinstance(value, int | float):
                formatted_items.append(f"{key}: {value}")
            else:
                # Truncate long strings
                str_value = str(value) if value is not None else "NULL"
                if len(str_value) > 30:
                    str_value = str_value[:27] + "..."
                formatted_items.append(f"{key}: {str_value}")

        return "{" + ", ".join(formatted_items) + "}"

    def display_demo_summary(self):
        """Display a summary of the demonstration results."""
        if not self.demo_results:
            print("No demo results to summarize")
            return

        print("\n" + "=" * 60)
        print("📋 DEMONSTRATION SUMMARY")
        print("=" * 60)

        total_queries = len(self.demo_results)
        successful_queries = sum(1 for r in self.demo_results if r.get("success", False))

        print(f"Total Queries Tested: {total_queries}")
        print(f"Successful Queries: {successful_queries}")
        print(f"Success Rate: {(successful_queries/total_queries)*100:.1f}%")

        if successful_queries > 0:
            successful_results = [r for r in self.demo_results if r.get("success", False)]
            avg_execution_time = sum(r["execution_time"] for r in successful_results) / len(
                successful_results
            )
            total_results = sum(r.get("result_count", 0) for r in successful_results)

            print(f"Average Execution Time: {avg_execution_time:.3f}s")
            print(f"Total Results Retrieved: {total_results}")

        # Show failed queries if any
        failed_queries = [r for r in self.demo_results if not r.get("success", False)]
        if failed_queries:
            print(f"\n❌ Failed Queries ({len(failed_queries)}):")
            for failed in failed_queries:
                print(f"   • {failed['query']}")
                if "error" in failed:
                    print(f"     Error: {failed['error']}")

    def run_interactive_mode(self):
        """Run an interactive query session."""
        if not self.sql_agent:
            print("❌ SQL Agent not initialized")
            return

        print("\n" + "=" * 60)
        print("🎮 INTERACTIVE TEXT-TO-SQL SESSION")
        print("=" * 60)
        print("Ask questions about the workshop database in natural language.")
        print("Type 'help' for examples, 'schema' to see database structure, or 'quit' to exit.\n")

        while True:
            try:
                user_query = input("💬 Your question: ").strip()

                if user_query.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break
                elif user_query.lower() == "help":
                    self._show_help()
                    continue
                elif user_query.lower() == "schema":
                    self.display_schema_overview()
                    continue
                elif not user_query:
                    continue

                print(f"\n🔍 Processing: {user_query}")
                print("-" * 50)

                self._process_demo_query(user_query)
                print("\n" + "-" * 50 + "\n")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

    def _show_help(self):
        """Show help information for interactive mode."""
        print("\n📖 HELP - Example Questions You Can Ask:")
        print("-" * 50)
        print("Basic Queries:")
        print("  • How many customers do we have?")
        print("  • Show me all products under $50")
        print("  • What customers are from New York?")
        print("\nAnalytics:")
        print("  • Who are our top 5 customers by spending?")
        print("  • What's the total revenue by category?")
        print("  • Show me average order value by state")
        print("\nTime-based:")
        print("  • What orders were placed this month?")
        print("  • Show me revenue trends over time")
        print("  • Find customers who haven't ordered recently")
        print("\nCommands:")
        print("  • 'schema' - Show database structure")
        print("  • 'help' - Show this help message")
        print("  • 'quit' - Exit interactive mode\n")

    def run_full_demo(self):
        """Run the complete demonstration."""
        print("🚀 Starting Text-to-SQL Workshop Demo")
        print("=" * 60)

        # Initialize
        if not self.initialize_agent():
            print("❌ Failed to initialize. Exiting.")
            return

        # Show schema
        self.display_schema_overview()

        # Run demo queries
        self.run_demo_queries()

        # Show summary
        self.display_demo_summary()

        # Offer interactive mode
        print("\n🎮 Ready for interactive mode!")
        response = input("Would you like to try asking your own questions? (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            self.run_interactive_mode()


def main():
    """Main function to run the Text-to-SQL demo."""
    # Database configuration
    db_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "workshop_db"),
        "user": os.getenv("DB_USER", "workshop_user"),
        "password": os.getenv("DB_PASSWORD", "workshop_pass"),
    }

    # AWS configuration (using LocalStack for local development)
    aws_endpoint = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")

    try:
        # Create and run demo
        demo = TextToSQLDemo(db_params, aws_endpoint)
        demo.run_full_demo()

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
