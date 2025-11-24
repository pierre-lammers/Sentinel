from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.vectorstores import InMemoryVectorStore
import warnings, os

warnings.filterwarnings("ignore", message=".*Google will stop supporting.*")


try:
    file_path = os.getenv("SRS_PATH")
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200, 
        add_start_index=True,
    )
    all_splits = text_splitter.split_documents(docs)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # 3. Vector Store
    vector_store = InMemoryVectorStore(embeddings)
    vector_store.add_documents(documents=all_splits)
    print("RAG: Vector Store chargé avec succès.")

except Exception as e:
    print(f"RAG WARNING: Erreur lors du chargement initial du RAG : {e}. L'Agent RAG ne fonctionnera pas.")
    vector_store = None


# --- Prompt Dynamique (Middleware pour l'Agent RAG) ---

@dynamic_prompt
def prompt_with_context(request: ModelRequest) -> str:
    """Injecte le contexte RAG dans les messages d'état de l'Agent."""
    
    if vector_store is None:
        return "You are a helpful assistant. Context is unavailable."

    last_query = request.state["messages"][-1].content
    
    retrieved_docs = vector_store.similarity_search(last_query)

    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    system_message = (
        "You are a helpful assistant specialized in technical documentation. "
        "Use ONLY the following context to answer the user's question. "
        "If the context does not contain the answer, state that you cannot find it.\n\n"
        f"Context:\n{docs_content}"
    )

    return system_message
