# Sample Markdown Document

## Overview

This is a sample markdown file used for testing the ingestion pipeline.

## Key Concepts

### Chunking
Documents are split into overlapping chunks to preserve context across boundaries.
Each chunk carries metadata: source file, page number, chunk index, and a unique document ID.

### Embeddings
Each chunk is converted to a vector using an embedding model.
These vectors are stored in ChromaDB for fast similarity search.

### Retrieval
When a user asks a question, the question is embedded and compared against stored chunks.
The most semantically similar chunks are returned as context.

## Conclusion

RAG systems combine retrieval and generation to produce accurate, grounded answers.
