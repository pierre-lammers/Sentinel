"""Utility functions for the test coverage pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_mistralai import MistralAIEmbeddings
from mistralai import Mistral

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


def get_mistral_client() -> Mistral:
    """Return the Mistral client."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set")
    return Mistral(api_key=api_key)


async def find_scenario_files(req_name: str) -> list[str]:
    """Find XML scenario files for a requirement using deep agent."""
    from agent.deep_agent import find_requirement_files

    # Use deep agent to find all files for the requirement
    all_files = await find_requirement_files(req_name, verbose=False)

    # Filter to keep only scenario XML files (pattern: scenario_*.xml)
    scenario_files = [
        f
        for f in all_files
        if Path(f).name.startswith("scenario_") and f.endswith(".xml")
    ]

    return scenario_files
