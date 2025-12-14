"""Utility functions for the test coverage pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from mistralai import Mistral

DATASET_PATH = Path(__file__).parent.parent.parent / "dataset"


def get_vector_store() -> Chroma:
    """Return the Chroma vector store."""
    return Chroma(
        collection_name="srs_db",
        embedding_function=GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001"
        ),
        persist_directory="./rag_srs_chroma_db",
    )


def get_mistral_client() -> Mistral:
    """Return the Mistral client."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set")
    return Mistral(api_key=api_key)


def find_scenario_files(req_name: str) -> list[str]:
    """Find XML scenario files for a requirement."""
    req_folder = DATASET_PATH / f"TS_{req_name}"
    if not req_folder.exists():
        return []
    return [
        str(f)
        for test_dir in sorted(req_folder.glob("test_*"))
        if test_dir.is_dir()
        for f in test_dir.glob("scenario_*.xml")
    ]
