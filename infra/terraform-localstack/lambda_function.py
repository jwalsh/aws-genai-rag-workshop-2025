import json
import os
import boto3

def handler(event, context):
    """
    RAG processor Lambda function for LocalStack testing
    """
    print(f"Processing event: {json.dumps(event)}")
    
    # Get environment variables
    docs_bucket = os.environ.get('DOCUMENTS_BUCKET')
    embeddings_bucket = os.environ.get('EMBEDDINGS_BUCKET')
    vector_table = os.environ.get('VECTOR_TABLE')
    opensearch_domain = os.environ.get('OPENSEARCH_DOMAIN')
    
    # Initialize AWS clients (pointing to LocalStack)
    s3 = boto3.client('s3', endpoint_url='http://localstack:4566')
    dynamodb = boto3.client('dynamodb', endpoint_url='http://localstack:4566')
    
    # Process the event
    if event.get('action') == 'process_document':
        document_key = event.get('document_key')
        
        # Simulate document processing
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document processed successfully',
                'document_key': document_key,
                'chunks_created': 10,
                'embeddings_stored': True
            })
        }
    else:
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'RAG processor ready',
                'environment': {
                    'docs_bucket': docs_bucket,
                    'embeddings_bucket': embeddings_bucket,
                    'vector_table': vector_table,
                    'opensearch_domain': opensearch_domain
                }
            })
        }
    
    return response