"""
SQL Agent for Natural Language to SQL Conversion

This module provides functionality to convert natural language queries
into SQL statements using AWS Bedrock and PostgreSQL database introspection.
"""

import logging
import re
import psycopg2
import boto3
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    columns: List[Dict[str, str]]
    foreign_keys: List[Dict[str, str]]
    description: Optional[str] = None


@dataclass
class QueryResult:
    """Result of a SQL query execution."""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    query: Optional[str] = None
    execution_time: Optional[float] = None


class DatabaseIntrospector:
    """Extracts schema information from PostgreSQL database."""
    
    def __init__(self, connection_params: Dict[str, str]):
        self.connection_params = connection_params
        
    def get_schema_info(self, schema_name: str = 'workshop') -> Dict[str, TableInfo]:
        """Extract complete schema information."""
        schema_info = {}
        
        try:
            with psycopg2.connect(**self.connection_params) as conn:
                with conn.cursor() as cursor:
                    # Get all tables in the schema
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """, (schema_name,))
                    
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    for table in tables:
                        schema_info[table] = self._get_table_info(cursor, schema_name, table)
                        
        except Exception as e:
            logger.error(f"Error extracting schema info: {e}")
            raise
            
        return schema_info
    
    def _get_table_info(self, cursor, schema_name: str, table_name: str) -> TableInfo:
        """Get detailed information about a specific table."""
        # Get column information
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema_name, table_name))
        
        columns = []
        for row in cursor.fetchall():
            col_info = {
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3],
                'max_length': row[4]
            }
            columns.append(col_info)
        
        # Get foreign key relationships
        cursor.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
        """, (schema_name, table_name))
        
        foreign_keys = []
        for row in cursor.fetchall():
            fk_info = {
                'column': row[0],
                'references_table': row[1],
                'references_column': row[2]
            }
            foreign_keys.append(fk_info)
        
        return TableInfo(
            name=table_name,
            columns=columns,
            foreign_keys=foreign_keys
        )


class SQLSecurityValidator:
    """Validates SQL queries for security and safety."""
    
    # Dangerous SQL patterns that should be blocked
    DANGEROUS_PATTERNS = [
        r'\bDROP\b',
        r'\bDELETE\b(?!\s+.*\bWHERE\b)',  # DELETE without WHERE
        r'\bTRUNCATE\b',
        r'\bALTER\b',
        r'\bCREATE\b',
        r'\bINSERT\b',
        r'\bUPDATE\b(?!\s+.*\bWHERE\b)',  # UPDATE without WHERE
        r'\bGRANT\b',
        r'\bREVOKE\b',
        r';.*?;',  # Multiple statements
        r'--',     # SQL comments
        r'/\*.*?\*/',  # Block comments
    ]
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a SQL query is safe to execute.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        query_upper = query.upper().strip()
        
        # Check if query starts with SELECT
        if not query_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return False, f"Query contains potentially dangerous pattern: {pattern}"
        
        # Check for excessive complexity (simple heuristics)
        if query.count('(') > 10 or query.count('JOIN') > 5:
            return False, "Query is too complex"
        
        if len(query) > 2000:
            return False, "Query is too long"
        
        return True, None


class BedrockNL2SQL:
    """Natural Language to SQL conversion using AWS Bedrock."""
    
    def __init__(self, region_name: str = 'us-east-1', endpoint_url: Optional[str] = None):
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=region_name,
            endpoint_url=endpoint_url
        )
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def generate_sql(self, natural_query: str, schema_info: Dict[str, TableInfo]) -> str:
        """Convert natural language to SQL using Bedrock."""
        schema_description = self._format_schema_for_prompt(schema_info)
        
        prompt = f"""You are a SQL expert. Convert the following natural language query to a PostgreSQL SELECT statement.

Database Schema:
{schema_description}

Natural Language Query: {natural_query}

Important Guidelines:
1. Only generate SELECT statements
2. Use proper table aliases
3. Join tables when needed using foreign key relationships
4. Use appropriate WHERE clauses
5. Format the output nicely with proper indentation
6. Don't include any explanations, just return the SQL query
7. Ensure the query is PostgreSQL compatible

SQL Query:"""

        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            sql_query = response_body['content'][0]['text'].strip()
            
            # Clean up the response - remove any markdown formatting
            sql_query = re.sub(r'```sql\s*', '', sql_query)
            sql_query = re.sub(r'```\s*$', '', sql_query)
            sql_query = sql_query.strip()
            
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL with Bedrock: {e}")
            raise
    
    def _format_schema_for_prompt(self, schema_info: Dict[str, TableInfo]) -> str:
        """Format schema information for the prompt."""
        schema_text = ""
        
        for table_name, table_info in schema_info.items():
            schema_text += f"\nTable: {table_name}\n"
            schema_text += "Columns:\n"
            
            for col in table_info.columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                schema_text += f"  - {col['name']} ({col['type']}) {nullable}\n"
            
            if table_info.foreign_keys:
                schema_text += "Foreign Keys:\n"
                for fk in table_info.foreign_keys:
                    schema_text += f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"
            
            schema_text += "\n"
        
        return schema_text


class SQLAgent:
    """Main SQL Agent class that orchestrates NL2SQL conversion and execution."""
    
    def __init__(self, 
                 db_connection_params: Dict[str, str],
                 aws_region: str = 'us-east-1',
                 aws_endpoint_url: Optional[str] = None):
        self.db_params = db_connection_params
        self.introspector = DatabaseIntrospector(db_connection_params)
        self.nl2sql = BedrockNL2SQL(aws_region, aws_endpoint_url)
        self.validator = SQLSecurityValidator()
        self.schema_cache = None
        self.cache_timestamp = None
        
    def refresh_schema(self, schema_name: str = 'workshop') -> None:
        """Refresh the cached schema information."""
        logger.info("Refreshing database schema cache...")
        self.schema_cache = self.introspector.get_schema_info(schema_name)
        self.cache_timestamp = datetime.now()
        logger.info(f"Cached schema for {len(self.schema_cache)} tables")
    
    def query(self, natural_language_query: str, schema_name: str = 'workshop') -> QueryResult:
        """
        Process a natural language query and return results.
        
        Args:
            natural_language_query: The question in natural language
            schema_name: Database schema to query (default: 'workshop')
            
        Returns:
            QueryResult object containing the results or error information
        """
        start_time = datetime.now()
        
        try:
            # Ensure schema cache is available
            if not self.schema_cache:
                self.refresh_schema(schema_name)
            
            # Generate SQL from natural language
            logger.info(f"Converting to SQL: {natural_language_query}")
            sql_query = self.nl2sql.generate_sql(natural_language_query, self.schema_cache)
            logger.info(f"Generated SQL: {sql_query}")
            
            # Validate the generated SQL
            is_valid, error_msg = self.validator.validate_query(sql_query)
            if not is_valid:
                return QueryResult(
                    success=False,
                    error=f"Generated query failed validation: {error_msg}",
                    query=sql_query
                )
            
            # Execute the query
            result = self._execute_query(sql_query)
            result.execution_time = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _execute_query(self, sql_query: str) -> QueryResult:
        """Execute a SQL query and return formatted results."""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query)
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Fetch all results
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            # Handle datetime objects
                            if hasattr(value, 'isoformat'):
                                row_dict[columns[i]] = value.isoformat()
                            else:
                                row_dict[columns[i]] = value
                        data.append(row_dict)
                    
                    return QueryResult(
                        success=True,
                        data=data,
                        query=sql_query
                    )
                    
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return QueryResult(
                success=False,
                error=str(e),
                query=sql_query
            )
    
    def get_schema_summary(self) -> str:
        """Get a human-readable summary of the database schema."""
        if not self.schema_cache:
            self.refresh_schema()
        
        summary = "Database Schema Summary:\n\n"
        
        for table_name, table_info in self.schema_cache.items():
            summary += f"=� Table: {table_name}\n"
            summary += f"   Columns: {len(table_info.columns)}\n"
            
            # Show key columns
            key_columns = [col['name'] for col in table_info.columns[:5]]
            if len(table_info.columns) > 5:
                key_columns.append("...")
            summary += f"   Key fields: {', '.join(key_columns)}\n"
            
            # Show relationships
            if table_info.foreign_keys:
                relationships = [f"{fk['column']} -> {fk['references_table']}" 
                               for fk in table_info.foreign_keys]
                summary += f"   Relationships: {', '.join(relationships)}\n"
            
            summary += "\n"
        
        return summary


def main():
    """Example usage of the SQL Agent."""
    # Database connection parameters (adjust for your setup)
    db_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'workshop_db',
        'user': 'workshop_user',
        'password': 'workshop_pass'
    }
    
    # AWS Bedrock endpoint (use LocalStack for local development)
    aws_endpoint = "http://localhost:4566"
    
    try:
        # Initialize the SQL agent
        agent = SQLAgent(db_params, aws_endpoint_url=aws_endpoint)
        
        # Print schema summary
        print("=== Database Schema ===")
        print(agent.get_schema_summary())
        
        # Example queries
        test_queries = [
            "Show me all customers from California",
            "What are the top 5 best-selling products?",
            "Find all orders placed in November 2024",
            "Which customers have spent more than $200?",
            "Show me the total revenue by product category"
        ]
        
        for query in test_queries:
            print(f"\n=== Query: {query} ===")
            result = agent.query(query)
            
            if result.success:
                print(f"SQL: {result.query}")
                print(f"Results: {len(result.data)} rows")
                if result.data:
                    # Show first few results
                    for i, row in enumerate(result.data[:3]):
                        print(f"  Row {i+1}: {row}")
                    if len(result.data) > 3:
                        print(f"  ... and {len(result.data) - 3} more rows")
            else:
                print(f"Error: {result.error}")
            
            print(f"Execution time: {result.execution_time:.2f}s")
            
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()