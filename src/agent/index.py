"""Script de création du vector store Chroma à partir du document SRS."""

from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders.parsers import TesseractBlobParser
from langchain_mistralai import MistralAIEmbeddings
from langchain_pymupdf4llm import PyMuPDF4LLMLoader  # type: ignore[import-untyped]
from langchain_text_splitters import RecursiveCharacterTextSplitter

root_dir = Path(__file__).parent.parent.parent
load_dotenv(root_dir / ".env")

# Load PDF with OCR for images
docs = PyMuPDF4LLMLoader(
    str(root_dir / "dataset" / "SRS.pdf"),
    mode="page",
    extract_images=True,
    images_parser=TesseractBlobParser(),
    table_strategy="lines",
).load()

# Split with optimized parameters for SRS requirements
all_splits = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=300,
    add_start_index=True,
    separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""],
).split_documents(docs)

# Enrich metadata for better retrieval
for i, split in enumerate(all_splits):
    split.metadata["chunk_index"] = i

# Index into Chroma
Chroma(
    collection_name="srs_db",
    embedding_function=MistralAIEmbeddings(model="mistral-embed"),
    persist_directory=str(root_dir / "rag_srs_chroma_db"),
).add_documents(documents=all_splits)
