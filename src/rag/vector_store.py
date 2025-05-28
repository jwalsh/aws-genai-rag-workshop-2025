"""Vector storage and retrieval using FAISS."""

import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for similarity search."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents = []
        self.metadata = []

    def add(self, embeddings: np.ndarray, documents: list[str],
            metadata: list[dict] | None = None):
        """Add embeddings and associated documents to the store."""
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} != {self.dimension}")

        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))

        # Store documents and metadata
        self.documents.extend(documents)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))

        logger.info(f"Added {len(documents)} documents to vector store")

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[dict[str, Any]]:
        """Search for k most similar documents."""
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for i, (idx, dist) in enumerate(zip(indices[0], distances[0], strict=False)):
            if idx < len(self.documents):
                results.append({
                    'index': int(idx),
                    'distance': float(dist),
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': float(1 / (1 + dist))  # Convert distance to score
                })

        return results

    def save(self, path: str):
        """Save vector store to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))

        # Save documents and metadata
        with open(path / "documents.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'dimension': self.dimension
            }, f)

        logger.info(f"Saved vector store to {path}")

    @classmethod
    def load(cls, path: str) -> 'FAISSVectorStore':
        """Load vector store from disk."""
        path = Path(path)

        # Load documents and metadata
        with open(path / "documents.pkl", 'rb') as f:
            data = pickle.load(f)

        # Create instance
        store = cls(data['dimension'])
        store.documents = data['documents']
        store.metadata = data['metadata']

        # Load FAISS index
        store.index = faiss.read_index(str(path / "index.faiss"))

        logger.info(f"Loaded vector store from {path}")
        return store

    def clear(self):
        """Clear the vector store."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self.metadata = []

    def size(self) -> int:
        """Return number of vectors in the store."""
        return self.index.ntotal


class DynamoDBVectorMetadata:
    """Store vector metadata in DynamoDB for scalability."""

    def __init__(self, table_name: str = "workshop-vector-metadata"):
        self.table_name = table_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from ..utils.aws_client import get_dynamodb_client
            self._client = get_dynamodb_client()
        return self._client

    def store_metadata(self, doc_id: str, metadata: dict[str, Any]):
        """Store document metadata in DynamoDB."""
        self.client.put_item(
            TableName=self.table_name,
            Item={
                'doc_id': {'S': doc_id},
                'metadata': {'S': json.dumps(metadata)},
                'timestamp': {'N': str(int(time.time()))}
            }
        )

    def get_metadata(self, doc_id: str) -> dict[str, Any] | None:
        """Retrieve document metadata from DynamoDB."""
        response = self.client.get_item(
            TableName=self.table_name,
            Key={'doc_id': {'S': doc_id}}
        )

        if 'Item' in response:
            return json.loads(response['Item']['metadata']['S'])
        return None
