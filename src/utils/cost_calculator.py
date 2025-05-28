"""Cost calculator for AWS GenAI services."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd


@dataclass
class ModelPricing:
    """Pricing information for a model."""

    model_id: str
    input_price_per_1k_tokens: float
    output_price_per_1k_tokens: float
    region: str = "us-east-1"


class AWSCostCalculator:
    """Calculator for AWS GenAI service costs."""

    # AWS Bedrock pricing as of 2025-05
    BEDROCK_PRICING = {
        "anthropic.claude-3-opus-20240229": ModelPricing(
            model_id="anthropic.claude-3-opus-20240229",
            input_price_per_1k_tokens=0.015,
            output_price_per_1k_tokens=0.075,
        ),
        "anthropic.claude-3-sonnet-20240229": ModelPricing(
            model_id="anthropic.claude-3-sonnet-20240229",
            input_price_per_1k_tokens=0.003,
            output_price_per_1k_tokens=0.015,
        ),
        "anthropic.claude-3-haiku-20240307": ModelPricing(
            model_id="anthropic.claude-3-haiku-20240307",
            input_price_per_1k_tokens=0.00025,
            output_price_per_1k_tokens=0.00125,
        ),
        "amazon.titan-embed-text-v2:0": ModelPricing(
            model_id="amazon.titan-embed-text-v2:0",
            input_price_per_1k_tokens=0.0002,
            output_price_per_1k_tokens=0.0,  # Embeddings have no output
        ),
        "cohere.embed-english-v3": ModelPricing(
            model_id="cohere.embed-english-v3",
            input_price_per_1k_tokens=0.0001,
            output_price_per_1k_tokens=0.0,
        ),
    }

    # Storage pricing
    S3_STORAGE_PRICE_PER_GB = 0.023  # Standard storage
    S3_REQUEST_PRICE = {"PUT": 0.005 / 1000, "GET": 0.0004 / 1000}  # per request  # per request

    def __init__(self):
        self.usage_history = []

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def calculate_llm_cost(
        self, model_id: str, input_text: str, output_text: str
    ) -> dict[str, float]:
        """Calculate cost for LLM usage."""
        if model_id not in self.BEDROCK_PRICING:
            raise ValueError(f"Unknown model: {model_id}")

        pricing = self.BEDROCK_PRICING[model_id]
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)

        input_cost = (input_tokens / 1000) * pricing.input_price_per_1k_tokens
        output_cost = (output_tokens / 1000) * pricing.output_price_per_1k_tokens

        return {
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }

    def calculate_embedding_cost(self, model_id: str, texts: list[str]) -> dict[str, float]:
        """Calculate cost for embedding generation."""
        if model_id not in self.BEDROCK_PRICING:
            raise ValueError(f"Unknown embedding model: {model_id}")

        pricing = self.BEDROCK_PRICING[model_id]
        total_tokens = sum(self.estimate_tokens(text) for text in texts)

        cost = (total_tokens / 1000) * pricing.input_price_per_1k_tokens

        return {
            "model_id": model_id,
            "num_texts": len(texts),
            "total_tokens": total_tokens,
            "total_cost": cost,
            "cost_per_text": cost / len(texts) if texts else 0,
        }

    def calculate_storage_cost(
        self, storage_gb: float, read_requests: int, write_requests: int, days: int = 30
    ) -> dict[str, float]:
        """Calculate S3 storage costs."""
        storage_cost = storage_gb * self.S3_STORAGE_PRICE_PER_GB * (days / 30)
        read_cost = read_requests * self.S3_REQUEST_PRICE["GET"]
        write_cost = write_requests * self.S3_REQUEST_PRICE["PUT"]

        return {
            "storage_gb": storage_gb,
            "storage_cost": storage_cost,
            "read_requests": read_requests,
            "read_cost": read_cost,
            "write_requests": write_requests,
            "write_cost": write_cost,
            "total_cost": storage_cost + read_cost + write_cost,
        }

    def track_usage(self, usage_data: dict):
        """Track usage for monitoring."""
        usage_data["timestamp"] = datetime.now().isoformat()
        self.usage_history.append(usage_data)

    def get_usage_summary(self, days: int = 7) -> pd.DataFrame:
        """Get usage summary for the last N days."""
        if not self.usage_history:
            return pd.DataFrame()

        df = pd.DataFrame(self.usage_history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Filter to last N days
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df["timestamp"] >= cutoff]

        return df
    
    def estimate_rag_costs(self, num_documents: int, avg_doc_size_kb: float,
                          queries_per_day: int, days: int = 30) -> dict:
        """Estimate costs for a RAG application."""
        # Estimate embeddings
        avg_chunks_per_doc = max(1, int(avg_doc_size_kb * 1024 / 2000))  # ~2000 chars per chunk
        total_chunks = num_documents * avg_chunks_per_doc
        
        # Embedding costs (one-time)
        embedding_model = "amazon.titan-embed-text-v2:0"
        embedding_cost = self.calculate_embedding_cost(
            embedding_model,
            ["sample"] * total_chunks  # Dummy texts for estimation
        )
        
        # Query costs (recurring)
        llm_model = "anthropic.claude-3-haiku-20240307"
        query_cost_per_day = self.calculate_llm_cost(
            llm_model,
            "What is the meaning of life?" * 10,  # ~40 tokens
            "The meaning of life is..." * 50  # ~200 tokens
        )['total_cost'] * queries_per_day
        
        # Storage costs
        storage_gb = (num_documents * avg_doc_size_kb) / (1024 * 1024)
        storage_cost = self.calculate_storage_cost(
            storage_gb,
            queries_per_day * days * 5,  # 5 reads per query
            total_chunks  # Initial writes
        )
        
        return {
            "setup_costs": {
                "embedding_generation": embedding_cost['total_cost'],
                "initial_storage": storage_cost['write_cost']
            },
            "monthly_costs": {
                "queries": query_cost_per_day * days,
                "storage": storage_cost['storage_cost'],
                "reads": storage_cost['read_cost']
            },
            "total_monthly": query_cost_per_day * days + storage_cost['total_cost'],
            "details": {
                "documents": num_documents,
                "chunks": total_chunks,
                "queries_per_day": queries_per_day,
                "storage_gb": round(storage_gb, 3)
            }
        }


# CLI interface
if __name__ == "__main__":
    import click
    
    @click.command()
    @click.option('--embeddings', default=1000, help='Number of embeddings')
    @click.option('--queries', default=100, help='Number of queries per day')
    @click.option('--storage-gb', default=0.1, help='Storage in GB')
    @click.option('--days', default=30, help='Number of days')
    def estimate(embeddings, queries, storage_gb, days):
        """Estimate RAG application costs."""
        calculator = AWSCostCalculator()
        
        # Estimate based on documents
        avg_doc_size = 50  # KB
        num_docs = int(embeddings / 10)  # Assume 10 chunks per doc
        
        costs = calculator.estimate_rag_costs(
            num_documents=num_docs,
            avg_doc_size_kb=avg_doc_size,
            queries_per_day=queries,
            days=days
        )
        
        click.echo("\n=== AWS RAG Cost Estimation ===")
        click.echo(f"\nSetup Costs (one-time):")
        for key, value in costs['setup_costs'].items():
            click.echo(f"  {key}: ${value:.4f}")
        
        click.echo(f"\nMonthly Costs:")
        for key, value in costs['monthly_costs'].items():
            click.echo(f"  {key}: ${value:.2f}")
        
        click.echo(f"\nTotal Monthly Cost: ${costs['total_monthly']:.2f}")
        
        click.echo(f"\nDetails:")
        for key, value in costs['details'].items():
            click.echo(f"  {key}: {value}")
    
    estimate()
