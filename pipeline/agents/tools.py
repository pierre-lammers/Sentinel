import warnings, os
import glob
import xml.etree.ElementTree as ET
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.documents import Document

warnings.filterwarnings("ignore", message=".*Google will stop supporting.*")

PERSIST_DIR = "./chroma_db_cache"
vector_store = None
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def load_xml_scenarios(directory_path):
    xml_docs = []
    # On cherche tous les fichiers .xml récursivement
    files = glob.glob(f"{directory_path}/**/*.xml", recursive=True)

 
    for file_path in files:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
                
            # --- STRATÉGIE D'APLATISSEMENT SÉMANTIQUE ---
            # Au lieu de donner le XML brut, on extrait les champs clés.
            # Adapte les balises ci-dessous (ex: 'Description', 'Steps') à TON schéma XML réel.
                
            scenario_name = root.find('Name').text if root.find('Name') is not None else "Sans Nom"
            description = root.find('Description').text if root.find('Description') is not None else ""
                
            # On consolide tout le contenu pertinent dans une chaîne texte riche
            content_content = f"""
            TYPE DE DOCUMENT: TEST FONCTIONNEL
            FICHIER: {os.path.basename(file_path)}
            SCENARIO: {scenario_name}
            DESCRIPTION: {description}
            CONTENU XML BRUT (EXTRAIT):
            {ET.tostring(root, encoding='unicode', method='xml')}
            """
                
            # On crée un Document LangChain manuel
            doc = Document(
                page_content=content_content,
                metadata={
                     "source": file_path,
                    "type": "TEST_XML", # Tag crucial pour le filtrage
                    "category": "functional_test"
                 }
            )
            xml_docs.append(doc)
                
        except Exception as e:
                print(f"Erreur lecture XML {file_path}: {e}")
        
    return xml_docs

try:
    # 1. Tenter de charger le Vector Store existant (Persistance)
    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
        print("RAG: Chargement du Vector Store à partir du cache (pas d'appel API).")
        # On charge la base Chroma existante
        vector_store = Chroma(
            persist_directory=PERSIST_DIR, 
            embedding_function=embeddings
        )
        print("RAG: Vector Store chargé depuis le cache avec succès.")

    # 2. Si le Vector Store n'existe pas, procéder à l'intégration complète
    else:
        print("RAG: Cache non trouvé. Intégration complète des documents (appel API).")
        
        # A. Chargement et Splitting des documents PDF
        pdf_path = os.getenv("SRS_PATH")
        pdf_loader = PyPDFLoader(pdf_path)
        pdf_docs = pdf_loader.load()

        # Splitter pour le texte (PDF)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200,
            add_start_index=True,
        )
        pdf_splits = text_splitter.split_documents(pdf_docs)
        for doc in pdf_splits:
            doc.metadata["type"] = "SPECIFICATION_DOC"
        print(f"RAG: {len(pdf_splits)} chunks de documentation traités.")

        # B. Chargement des Tests (XML)
        test_path = os.getenv("TESTS_PATH")
        # Pour intégrer TOUS les tests, assurez-vous de supprimer ici toute restriction 
        # (ex: la condition 'if "TS_MSAW" in file_path:' dans load_xml_scenarios)
        xml_test_docs = load_xml_scenarios(test_path) 
        print(f"RAG: {len(xml_test_docs)} fichiers de tests XML traités.")

        # C. Fusion des connaissances
        all_documents = pdf_splits + xml_test_docs

        # D. Création et persistance du Vector Store
        vector_store = Chroma.from_documents(
            documents=all_documents,
            embedding=embeddings,
            persist_directory=PERSIST_DIR
        )
        # On appelle persist() pour être sûr d'écrire sur le disque immédiatement
        vector_store.persist() 
        print("RAG: Vector Store complet (Docs + Tests) créé et sauvegardé avec succès.")

except Exception as e:
    print(f"RAG WARNING: Erreur critique : {e}")
    vector_store = None


# --- Prompt Dynamique (Middleware pour l'Agent RAG) ---

@dynamic_prompt
def retrieve_tech_doc_context(request: ModelRequest) -> str:
    """
    Injects context from technical specification documents ONLY.
    Filters the vector store results to include 'SPECIFICATION_DOC' type only.
    This agent answers pure informational/technical queries.
    """
    if vector_store is None:
        return "You are a helpful assistant. Context is unavailable."

    last_query = request.state["messages"][-1].content
    
    # 1. Perform wide search on the full index
    retrieved_docs_raw = vector_store.similarity_search(last_query, k=10) 
    
    # 2. Filter for 'SPECIFICATION_DOC' and limit context size
    spec_docs = [
        doc for doc in retrieved_docs_raw 
        if doc.metadata.get("type") == "SPECIFICATION_DOC"
    ][:4] 

    docs_content = "\n\n".join(doc.page_content for doc in spec_docs)

    # 3. Build system message
    if not docs_content:
         system_message = (
            "You are a helpful assistant specialized in technical documentation. "
            "I searched the SPECIFICATION DOCUMENTATION but found no relevant context for the query. "
            "State clearly that the information cannot be found in the provided technical documentation."
        )
    else:
        system_message = (
            "You are a helpful assistant specialized in technical documentation. "
            "Use ONLY the following context, extracted from the SPECIFICATION DOCUMENTATION, to answer the user's question. "
            "If the context does not contain the answer, state that you cannot find it.\n\n"
            f"Context:\n{docs_content}"
        )

    return system_message


@dynamic_prompt
def analyze_coverage_context(request: ModelRequest) -> str:
    """
    Injects a hybrid context (SPECIFICATION + TESTS) for coverage analysis.
    The agent uses this context to compare requirements against functional test scenarios.
    
    This prompt is optimized for conciseness and structured output (Fully Covered, Partially Covered, Not Covered).
    """
    
    if vector_store is None:
        return "You are a highly concise QA Coverage Expert. Context is unavailable."

    last_query = request.state["messages"][-1].content
    
    # 1. Retrieve Specification chunks (Source of truth)
    try:
        spec_docs = vector_store.similarity_search(
            query=last_query, 
            k=2,
            filter={"type": "SPECIFICATION_DOC"}
        )
    except Exception as e:
        print(f"RAG WARNING: Erreur de recherche SPEC_DOC: {e}")
        spec_docs = []

    # 2. Retrieve Test chunks (Verification data)
    try:
        test_docs = vector_store.similarity_search(
            query=last_query,
            k=4, # On limite directement à 4 chunks
            filter={"type": "TEST_XML"} # <-- Recherche ciblée sur le type
        )
    except Exception as e:
        print(f"RAG WARNING: Erreur de recherche TEST_XML: {e}")
        test_docs = []

    # 3. Construct context sections (clearly labeled for the LLM)
    spec_content = "\n\n--- SPECIFICATION (REQUIREMENT) ---\n" + "\n".join(doc.page_content for doc in spec_docs)
    test_content = "\n\n--- FUNCTIONAL TESTS (SCENARIOS) ---\n" + "\n".join(doc.page_content for doc in test_docs)

    docs_content = spec_content + "\n" + test_content

    # 4. Build system message with strict instructions for structured output
    if not spec_docs:
        print("not spec_docs")
        # This system message forces the agent to output a single, non-empty text string in French.
        system_message = (
            "You are a highly concise QA Coverage Expert. "
            "The search for the requirement in the technical documentation returned no relevant content. "
            "Your ONLY response must be a single, short sentence in English stating: "
            "'Le document de spécification technique ne contient aucune information pertinente pour l\'exigence demandée. L\'analyse de couverture est impossible.'"
         )
        return system_message

    system_message = (
        "You are a highly concise QA Coverage Expert. Your sole task is to analyze the coverage status of the requirements "
        "found in the SPECIFICATION against the provided FUNCTIONAL TESTS. "
        "Based ONLY on the CONTEXTE D'ANALYSE provided, follow these strict output guidelines:\n"
        
        "1. For each requirement identified in the context, evaluate its coverage status using one of these three labels:\n"
        "   - **Fully Covered**\n"
        "   - **Partially Covered**\n"
        "   - **Not Covered**\n"
        
        "2. If the status is 'Partially Covered' or 'Not Covered', you MUST explicitly list the missing test conditions or test cases."
        
        "3. Present the result as a structured list or table, focusing only on the analysis, without any conversational preamble or conclusion."
        "4. Output must be in French.\n\n"
        
        f"CONTEXTE D'ANALYSE:\n{docs_content}"
    )

    return system_message