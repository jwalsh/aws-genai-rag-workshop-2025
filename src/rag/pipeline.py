"""Main RAG pipeline implementation."""

import json
import logging
from dataclasses import dataclass
from typing import Any

import click

from ..utils.aws_client import get_bedrock_runtime_client
from .chunking import SimpleChunker
from .embeddings import EmbeddingGenerator
from .vector_store import FAISSVectorStore

logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""

    chunk_size: int = 512
    chunk_overlap: int = 50
    embedding_model: str = "all-MiniLM-L6-v2"  # Use local model by default
    retrieval_k: int = 5
    rerank: bool = True


class RAGPipeline:
    """Production-ready RAG pipeline."""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.chunker = SimpleChunker(
            chunk_size=config.chunk_size, overlap=config.chunk_overlap
        )
        self.embedder = EmbeddingGenerator(
            model_name=config.embedding_model,
            use_bedrock="titan" in config.embedding_model
        )
        # Initialize vector store with embedding dimension
        dimension = 384 if "MiniLM" in config.embedding_model else 1536
        self.vector_store = FAISSVectorStore(dimension=dimension)
        self.bedrock = None  # Lazy load when needed

    def process_documents(self, documents: list[str]) -> None:
        """Process and index documents."""
        logger.info(f"Processing {len(documents)} documents")

        # Chunk documents
        all_chunks = []
        chunk_texts = []
        for doc in documents:
            chunks = self.chunker.chunk_text(doc)
            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_texts.append(chunk['text'])

        # Generate embeddings
        embeddings = self.embedder.generate(chunk_texts)

        # Store in vector database
        self.vector_store.add(
            embeddings=embeddings,
            documents=chunk_texts,
            metadata=all_chunks
        )

        logger.info(f"Indexed {len(all_chunks)} chunks")

    def query(self, question: str) -> dict[str, Any]:
        """Query the RAG system."""
        logger.info(f"Querying: {question}")

        # Generate query embedding
        query_embedding = self.embedder.generate(question)

        # Retrieve relevant chunks
        results = self.vector_store.search(
            query_embedding=query_embedding[0],
            k=self.config.retrieval_k
        )

        # Extract documents
        relevant_chunks = [r['document'] for r in results]

        # Build context
        context = "\n\n".join(relevant_chunks)

        # Generate response using Bedrock
        response = self._generate_response(question, context)

        return {
            "question": question,
            "answer": response,
            "sources": relevant_chunks,
            "scores": [r['score'] for r in results],
            "metadata": {
                "chunks_used": len(relevant_chunks),
                "model": self.config.embedding_model
            },
        }

    def _generate_response(self, question: str, context: str) -> str:
        """Generate response using Bedrock."""
        if self.bedrock is None:
            self.bedrock = get_bedrock_runtime_client()

        prompt = f"""Context information:
{context}

Question: {question}

Based on the context above, please provide a comprehensive answer to the question."""

        try:
            # Example for Claude model
            body = json.dumps({
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 500,
                "temperature": 0.7
            })

            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-instant-v1",
                body=body
            )

            result = json.loads(response['body'].read())
            return result.get('completion', 'Unable to generate response')
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: {e!s}"


@click.group()
def cli():
    """RAG Pipeline CLI."""
    pass


@cli.command()
@click.option('--source', required=True, help='Source file or S3 path')
@click.option('--chunks', default=100, help='Max chunks to process')
def process(source: str, chunks: int):
    """Process documents and create embeddings."""
    config = RAGConfig()
    pipeline = RAGPipeline(config)

    # Load document
    if source.endswith('.pdf'):
        from ..utils.pdf_extractor import PDFExtractor
        extractor = PDFExtractor()
        # Extract limited pages to avoid processing whole PDF
        max_pages = chunks // 10  # Roughly 10 chunks per page
        text = extractor.extract_text(source, max_pages=max_pages)
    else:
        with open(source) as f:
            text = f.read()

    pipeline.process_documents([text])
    pipeline.vector_store.save("data/vector_store")
    click.echo(f"Processed {source} into {pipeline.vector_store.size()} vectors")


@cli.command()
@click.option('--question', required=True, help='Question to ask')
def query(question: str):
    """Query the RAG system."""
    config = RAGConfig()
    pipeline = RAGPipeline(config)

    # Load vector store
    pipeline.vector_store = FAISSVectorStore.load("data/vector_store")

    result = pipeline.query(question)
    click.echo(f"\nQuestion: {result['question']}")
    click.echo(f"\nAnswer: {result['answer']}")
    click.echo(f"\nSources used: {len(result['sources'])}")


if __name__ == "__main__":
    cli()
