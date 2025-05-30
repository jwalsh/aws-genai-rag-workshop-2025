# Bedrock Knowledge Base management
import boto3
import json
import time
from typing import Dict, Any, List, Optional
from enum import Enum


class ChunkingStrategy(Enum):
    FIXED = "FIXED_SIZE"
    SEMANTIC = "SEMANTIC"
    HIERARCHICAL = "HIERARCHICAL"
    NONE = "NONE"


class KnowledgeBaseManager:
    """Manages Bedrock Knowledge Bases"""
    
    def __init__(self, region_name='us-east-1'):
        self.region = region_name
        self.session = boto3.Session(region_name=region_name)
        self.bedrock_agent = self.session.client('bedrock-agent')
        self.bedrock_runtime = self.session.client('bedrock-agent-runtime')
        
    def create_knowledge_base(self, 
                            name: str,
                            role_arn: str,
                            embedding_model_id: str,
                            opensearch_collection_arn: str,
                            index_name: str,
                            description: str = "") -> str:
        """Create a Bedrock Knowledge Base"""
        
        storage_config = {
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": opensearch_collection_arn,
                "vectorIndexName": index_name,
                "fieldMapping": {
                    "vectorField": "embedding",
                    "textField": "text",
                    "metadataField": "metadata"
                }
            }
        }
        
        response = self.bedrock_agent.create_knowledge_base(
            name=name,
            description=description,
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": f"arn:aws:bedrock:{self.region}::foundation-model/{embedding_model_id}"
                }
            },
            storageConfiguration=storage_config
        )
        
        return response['knowledgeBase']['knowledgeBaseId']
    
    def create_data_source(self,
                         knowledge_base_id: str,
                         name: str,
                         s3_bucket_name: str,
                         s3_prefix: str = "",
                         chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
                         max_tokens: int = 300,
                         overlap_percentage: int = 10) -> str:
        """Create a data source for the knowledge base"""
        
        data_source_config = {
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{s3_bucket_name}",
            }
        }
        
        if s3_prefix:
            data_source_config["s3Configuration"]["inclusionPrefixes"] = [s3_prefix]
        
        # Configure chunking strategy
        vector_ingestion_config = {
            "chunkingConfiguration": self._get_chunking_config(
                chunking_strategy, max_tokens, overlap_percentage
            )
        }
        
        response = self.bedrock_agent.create_data_source(
            knowledgeBaseId=knowledge_base_id,
            name=name,
            dataSourceConfiguration=data_source_config,
            vectorIngestionConfiguration=vector_ingestion_config
        )
        
        return response['dataSource']['dataSourceId']
    
    def _get_chunking_config(self, strategy: ChunkingStrategy, 
                           max_tokens: int, overlap_percentage: int) -> Dict:
        """Get chunking configuration based on strategy"""
        if strategy == ChunkingStrategy.FIXED:
            return {
                "chunkingStrategy": "FIXED_SIZE",
                "fixedSizeChunkingConfiguration": {
                    "maxTokens": max_tokens,
                    "overlapPercentage": overlap_percentage
                }
            }
        elif strategy == ChunkingStrategy.SEMANTIC:
            return {
                "chunkingStrategy": "SEMANTIC",
                "semanticChunkingConfiguration": {
                    "maxTokens": max_tokens,
                    "bufferSize": 0,
                    "breakpointPercentileThreshold": 95
                }
            }
        elif strategy == ChunkingStrategy.HIERARCHICAL:
            return {
                "chunkingStrategy": "HIERARCHICAL",
                "hierarchicalChunkingConfiguration": {
                    "levelConfigurations": [
                        {"maxTokens": 1500},
                        {"maxTokens": 300}
                    ],
                    "overlapTokens": 60
                }
            }
        else:
            return {"chunkingStrategy": "NONE"}
    
    def start_ingestion_job(self, knowledge_base_id: str, data_source_id: str) -> str:
        """Start an ingestion job to sync data"""
        response = self.bedrock_agent.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        
        # Wait for job to complete
        self._wait_for_ingestion_job(knowledge_base_id, data_source_id, job_id)
        
        return job_id
    
    def _wait_for_ingestion_job(self, kb_id: str, ds_id: str, job_id: str, 
                               max_wait: int = 600):
        """Wait for ingestion job to complete"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job_id
            )
            
            status = response['ingestionJob']['status']
            if status == 'COMPLETE':
                return True
            elif status == 'FAILED':
                raise Exception(f"Ingestion job failed: {response['ingestionJob']}")
            
            time.sleep(10)
        
        raise TimeoutError(f"Ingestion job did not complete within {max_wait} seconds")
    
    def retrieve(self, 
                knowledge_base_id: str,
                query: str,
                max_results: int = 5,
                search_type: str = "HYBRID") -> List[Dict]:
        """Retrieve relevant documents from knowledge base"""
        
        response = self.bedrock_runtime.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results,
                    'overrideSearchType': search_type
                }
            }
        )
        
        results = []
        for item in response['retrievalResults']:
            results.append({
                'content': item['content']['text'],
                'score': item.get('score', 0),
                'metadata': item.get('metadata', {}),
                'location': item.get('location', {})
            })
        
        return results
    
    def retrieve_and_generate(self,
                            knowledge_base_id: str,
                            query: str,
                            model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
                            max_results: int = 5,
                            temperature: float = 0.0) -> Dict[str, Any]:
        """Retrieve and generate response using RAG"""
        
        response = self.bedrock_runtime.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': f"arn:aws:bedrock:{self.region}::foundation-model/{model_id}",
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': max_results
                        }
                    },
                    'generationConfiguration': {
                        'inferenceConfig': {
                            'textInferenceConfig': {
                                'temperature': temperature,
                                'maxTokens': 2048
                            }
                        }
                    }
                }
            }
        )
        
        return {
            'response': response['output']['text'],
            'citations': response.get('citations', []),
            'session_id': response.get('sessionId')
        }