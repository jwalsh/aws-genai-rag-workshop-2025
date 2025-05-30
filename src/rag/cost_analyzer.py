# Cost analysis utilities for RAG
from typing import Dict, List, Optional


class CostAnalyzer:
    """Analyze costs for Bedrock RAG operations"""
    
    # Bedrock pricing per 1000 tokens (as of 2024)
    BEDROCK_MODEL_PRICING = {
        # Claude models
        "anthropic.claude-3-opus-20240229-v1:0": {
            "input": 0.015,
            "output": 0.075
        },
        "anthropic.claude-3-sonnet-20240229-v1:0": {
            "input": 0.003,
            "output": 0.015
        },
        "anthropic.claude-3-haiku-20240307-v1:0": {
            "input": 0.00025,
            "output": 0.00125
        },
        "anthropic.claude-v2:1": {
            "input": 0.008,
            "output": 0.024
        },
        "anthropic.claude-instant-v1": {
            "input": 0.0008,
            "output": 0.0024
        },
        
        # Titan models
        "amazon.titan-text-express-v1": {
            "input": 0.0002,
            "output": 0.0006
        },
        "amazon.titan-text-lite-v1": {
            "input": 0.00015,
            "output": 0.0002
        },
        "amazon.titan-embed-text-v1": {
            "input": 0.0001,
            "output": 0  # Embedding models don't have output tokens
        },
        "amazon.titan-embed-text-v2:0": {
            "input": 0.00002,
            "output": 0
        },
        
        # Cohere models
        "cohere.embed-english-v3": {
            "input": 0.0001,
            "output": 0
        },
        "cohere.embed-multilingual-v3": {
            "input": 0.0001,
            "output": 0
        }
    }
    
    def __init__(self):
        self.total_costs = {
            "embedding": 0.0,
            "generation": 0.0,
            "total": 0.0
        }
    
    def calculate_token_cost(self, 
                           model_id: str,
                           input_tokens: int,
                           output_tokens: int = 0) -> float:
        """Calculate cost for tokens based on model pricing"""
        if model_id not in self.BEDROCK_MODEL_PRICING:
            raise ValueError(f"Unknown model: {model_id}")
        
        pricing = self.BEDROCK_MODEL_PRICING[model_id]
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def estimate_embedding_cost(self,
                              texts: List[str],
                              model_id: str = "amazon.titan-embed-text-v2:0") -> Dict[str, float]:
        """Estimate cost for embedding texts"""
        # Rough estimation: 1 token ≈ 4 characters
        total_chars = sum(len(text) for text in texts)
        estimated_tokens = total_chars // 4
        
        cost = self.calculate_token_cost(model_id, estimated_tokens)
        
        return {
            "texts_count": len(texts),
            "estimated_tokens": estimated_tokens,
            "model": model_id,
            "estimated_cost": cost
        }
    
    def estimate_knowledge_base_cost(self,
                                   num_documents: int,
                                   avg_doc_size_chars: int,
                                   chunks_per_doc: int = 10,
                                   embedding_model: str = "amazon.titan-embed-text-v2:0") -> Dict[str, float]:
        """Estimate cost for creating a knowledge base"""
        total_chunks = num_documents * chunks_per_doc
        total_chars = num_documents * avg_doc_size_chars
        estimated_tokens = total_chars // 4
        
        embedding_cost = self.calculate_token_cost(embedding_model, estimated_tokens)
        
        # Storage cost estimation (OpenSearch Serverless)
        # Rough estimate: $0.024 per GB-hour
        storage_gb = (total_chars / 1e9) * 2  # Assume 2x storage for indices
        monthly_storage_cost = storage_gb * 0.024 * 24 * 30
        
        return {
            "documents": num_documents,
            "total_chunks": total_chunks,
            "estimated_tokens": estimated_tokens,
            "embedding_cost": embedding_cost,
            "monthly_storage_cost": monthly_storage_cost,
            "total_initial_cost": embedding_cost,
            "monthly_recurring_cost": monthly_storage_cost
        }
    
    def estimate_rag_query_cost(self,
                              query: str,
                              num_retrieved_chunks: int = 5,
                              avg_chunk_size: int = 300,
                              generation_model: str = "anthropic.claude-3-haiku-20240307-v1:0",
                              embedding_model: str = "amazon.titan-embed-text-v2:0") -> Dict[str, float]:
        """Estimate cost for a single RAG query"""
        # Query embedding cost
        query_tokens = len(query) // 4
        embedding_cost = self.calculate_token_cost(embedding_model, query_tokens)
        
        # Context tokens (retrieved chunks)
        context_tokens = num_retrieved_chunks * avg_chunk_size
        
        # Total input tokens for generation
        total_input_tokens = query_tokens + context_tokens
        
        # Estimate output tokens (assume 2x input for comprehensive response)
        output_tokens = total_input_tokens * 2
        
        # Generation cost
        generation_cost = self.calculate_token_cost(
            generation_model, 
            total_input_tokens, 
            output_tokens
        )
        
        total_cost = embedding_cost + generation_cost
        
        return {
            "query_length": len(query),
            "retrieved_chunks": num_retrieved_chunks,
            "context_tokens": context_tokens,
            "output_tokens": output_tokens,
            "embedding_cost": embedding_cost,
            "generation_cost": generation_cost,
            "total_cost": total_cost,
            "models": {
                "embedding": embedding_model,
                "generation": generation_model
            }
        }
    
    def track_actual_cost(self,
                        operation_type: str,
                        model_id: str,
                        input_tokens: int,
                        output_tokens: int = 0):
        """Track actual costs for operations"""
        cost = self.calculate_token_cost(model_id, input_tokens, output_tokens)
        
        if operation_type == "embedding":
            self.total_costs["embedding"] += cost
        else:
            self.total_costs["generation"] += cost
        
        self.total_costs["total"] = (
            self.total_costs["embedding"] + 
            self.total_costs["generation"]
        )
    
    def get_cost_summary(self) -> Dict[str, float]:
        """Get summary of tracked costs"""
        return self.total_costs.copy()
    
    def reset_cost_tracking(self):
        """Reset cost tracking"""
        self.total_costs = {
            "embedding": 0.0,
            "generation": 0.0,
            "total": 0.0
        }