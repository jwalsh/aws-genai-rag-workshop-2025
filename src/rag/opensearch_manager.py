# OpenSearch vector store management
import boto3
import json
import time
from typing import Dict, Any, List, Optional


class OpenSearchManager:
    """Manages OpenSearch Serverless collections for RAG"""
    
    def __init__(self, region_name='us-east-1'):
        self.region = region_name
        self.session = boto3.Session(region_name=region_name)
        self.oss_client = self.session.client('opensearchserverless')
        self.sts_client = self.session.client('sts')
        
    def create_opensearch_policies(self, collection_name: str) -> Dict[str, str]:
        """Create encryption and network policies for OpenSearch collection"""
        account_id = self.sts_client.get_caller_identity()['Account']
        
        # Create encryption policy
        encryption_policy = {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                }
            ],
            "AWSOwnedKey": True
        }
        
        self.oss_client.create_security_policy(
            name=f'{collection_name}-encryption',
            type='encryption',
            policy=json.dumps(encryption_policy)
        )
        
        # Create network policy
        network_policy = [{
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                },
                {
                    "ResourceType": "dashboard",
                    "Resource": [f"collection/{collection_name}"]
                }
            ],
            "AllowFromPublic": True
        }]
        
        self.oss_client.create_security_policy(
            name=f'{collection_name}-network',
            type='network',
            policy=json.dumps(network_policy)
        )
        
        return {
            'encryption_policy': f'{collection_name}-encryption',
            'network_policy': f'{collection_name}-network'
        }
    
    def create_opensearch_collection(self, collection_name: str) -> str:
        """Create OpenSearch Serverless collection"""
        try:
            response = self.oss_client.create_collection(
                name=collection_name,
                type='VECTORSEARCH',
                description='Vector search collection for RAG'
            )
            
            collection_id = response['createCollectionDetail']['id']
            
            # Wait for collection to be active
            self.wait_for_collection_active(collection_id)
            
            # Get collection endpoint
            collection_details = self.oss_client.batch_get_collection(
                ids=[collection_id]
            )
            
            return collection_details['collectionDetails'][0]['collectionEndpoint']
            
        except self.oss_client.exceptions.ConflictException:
            # Collection already exists
            collections = self.oss_client.list_collections(
                collectionFilters={'name': collection_name}
            )
            if collections['collectionSummaries']:
                collection_id = collections['collectionSummaries'][0]['id']
                collection_details = self.oss_client.batch_get_collection(
                    ids=[collection_id]
                )
                return collection_details['collectionDetails'][0]['collectionEndpoint']
    
    def wait_for_collection_active(self, collection_id: str, max_wait: int = 600):
        """Wait for OpenSearch collection to become active"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.oss_client.batch_get_collection(ids=[collection_id])
            if response['collectionDetails']:
                status = response['collectionDetails'][0]['status']
                if status == 'ACTIVE':
                    return True
                elif status == 'FAILED':
                    raise Exception(f"Collection creation failed")
            
            time.sleep(10)
        
        raise TimeoutError(f"Collection did not become active within {max_wait} seconds")
    
    def create_opensearch_index(self, collection_endpoint: str, index_name: str, 
                               embedding_dimension: int = 1536) -> bool:
        """Create index in OpenSearch collection"""
        import requests
        from requests_aws4auth import AWS4Auth
        
        credentials = self.session.get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.region,
            'aoss',
            session_token=credentials.token
        )
        
        index_body = {
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": embedding_dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "faiss"
                        }
                    },
                    "metadata": {"type": "object"}
                }
            },
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 512
                }
            }
        }
        
        response = requests.put(
            f"{collection_endpoint}/{index_name}",
            auth=awsauth,
            json=index_body,
            headers={"Content-Type": "application/json"}
        )
        
        return response.status_code == 200
    
    def create_opensearch_access_policy(self, collection_name: str, 
                                       principal_arns: List[str]) -> str:
        """Create data access policy for OpenSearch collection"""
        account_id = self.sts_client.get_caller_identity()['Account']
        
        access_policy = [{
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ]
                },
                {
                    "ResourceType": "index",
                    "Resource": [f"index/{collection_name}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument"
                    ]
                }
            ],
            "Principal": principal_arns
        }]
        
        response = self.oss_client.create_access_policy(
            name=f'{collection_name}-access',
            type='data',
            policy=json.dumps(access_policy)
        )
        
        return response['accessPolicyDetail']['name']