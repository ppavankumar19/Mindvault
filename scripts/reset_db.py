#!/usr/bin/env python3
"""Reset (delete) a ChromaDB collection."""

import argparse
import shutil
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Reset the vector store")
    parser.add_argument("--dir", default=os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db"))
    parser.add_argument("--yes", action="store_true", help="Skip confirmation")
    args = parser.parse_args()

    if not args.yes:
        confirm = input(f"Delete all data in '{args.dir}'? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            return

    if os.path.exists(args.dir):
        shutil.rmtree(args.dir)
        print(f"Deleted: {args.dir}")
    else:
        print("Nothing to delete.")


if __name__ == "__main__":
    main()
