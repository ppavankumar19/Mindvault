#!/usr/bin/env python3
"""Bulk ingest all documents from a folder into a collection."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.ingestion import load_folder
from core.embeddings import get_embedding_model
from core.vector_store import get_or_create_collection, add_documents


def main():
    parser = argparse.ArgumentParser(description="Bulk ingest documents from a folder")
    parser.add_argument("folder", help="Path to folder containing documents")
    parser.add_argument("--collection", default="my_knowledge_base", help="Collection name")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--overlap", type=int, default=150)
    args = parser.parse_args()

    print(f"Loading documents from: {args.folder}")
    embed_model = get_embedding_model()
    collection = get_or_create_collection(args.collection, embed_model)

    results = load_folder(args.folder, chunk_size=args.chunk_size, chunk_overlap=args.overlap)

    total_chunks = 0
    for chunks, doc_id in results:
        add_documents(collection, chunks)
        total_chunks += len(chunks)

    print(f"\nDone! {len(results)} documents, {total_chunks} total chunks ingested into '{args.collection}'")


if __name__ == "__main__":
    main()
