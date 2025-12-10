"""Script de création du vector store Chroma à partir du document SRS."""

from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders.parsers import TesseractBlobParser
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pymupdf4llm import PyMuPDF4LLMLoader  # type: ignore[import-untyped]
from langchain_text_splitters import RecursiveCharacterTextSplitter

root_dir = Path(__file__).parent.parent.parent
load_dotenv(root_dir / ".env")

srs_pdf_path = root_dir / "dataset" / "SRS.pdf"

loader = PyMuPDF4LLMLoader(
    str(srs_pdf_path),
    mode="page",
    extract_images=True,
    images_parser=TesseractBlobParser(),
    table_strategy="lines",
)

docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # chunk size (characters)
    chunk_overlap=200,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)
all_splits = text_splitter.split_documents(docs)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
)

chroma_db_path = root_dir / "rag_srs_chroma_db"

vector_store = Chroma(
    collection_name="srs_db",
    embedding_function=embeddings,
    persist_directory=str(
        chroma_db_path
    ),  # Where to save data locally, remove if not necessary
)

vector_store.add_documents(documents=all_splits)
