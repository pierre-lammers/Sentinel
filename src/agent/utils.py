"""Utility functions for the test coverage pipeline."""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_mistralai import MistralAIEmbeddings

DATASET_PATH = Path(__file__).parent.parent.parent / "dataset"


def get_vector_store() -> Chroma:
    """Return the Chroma vector store."""
    root_dir = Path(__file__).parent.parent.parent
    chroma_db_path = root_dir / "rag_srs_chroma_db"
    return Chroma(
        collection_name="srs_db",
        embedding_function=MistralAIEmbeddings(model="mistral-embed"),
        persist_directory=str(chroma_db_path),
    )
