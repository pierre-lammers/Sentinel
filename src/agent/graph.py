"""Pipeline RAG + Multi-LLM pour analyse de couverture de tests.

Ce module définit un graph LangGraph qui:
1. Récupère la description d'un requirement via RAG
2. Génère les test cases à couvrir (LLM1)
3. Analyse un scénario de test et marque les test cases couverts (LLM2)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

load_dotenv()


# =============================================================================
# Data Models
# =============================================================================


class TestCase(TypedDict):
    """Représentation d'un test case avec son statut de présence."""

    id: str
    description: str
    present: bool  # True si le test est couvert par le scénario


# =============================================================================
# Configuration Context
# =============================================================================


class Context(TypedDict, total=False):
    """Context de configuration pour la pipeline."""

    llm1_model: str  # Modèle pour génération des test cases
    llm2_model: str  # Modèle pour analyse du scénario
    rag_top_k: int  # Nombre de documents à récupérer
    temperature: float


# =============================================================================
# State Definition
# =============================================================================


class StateInput(TypedDict):
    """Schéma d'input pour la pipeline."""

    req_id: str  # ID du requirement à analyser
    test_scenario: str  # Contenu XML du scénario de test


@dataclass
class State:
    """État de la pipeline de couverture de tests."""

    # --- Inputs ---
    req_id: str = ""  # ID du requirement à analyser
    test_scenario: str = ""  # Contenu XML du scénario de test

    # --- Étape 1: RAG ---
    requirement_description: str = ""
    rag_context: str = ""

    # --- Étape 2: LLM1 - Génération des test cases ---
    generated_test_cases: List[str] = field(default_factory=list)

    # --- Étape 3: LLM2 - Analyse du scénario ---
    test_cases_with_status: List[TestCase] = field(default_factory=list)

    # --- Metadata ---
    errors: List[str] = field(default_factory=list)


# =============================================================================
# Utility Functions
# =============================================================================


def get_vector_store() -> Chroma:
    """Initialise et retourne le vector store Chroma."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    return Chroma(
        collection_name="srs_db",
        embedding_function=embeddings,
        persist_directory="./rag_srs_chroma_db",
    )


def get_llm(model: Optional[str] = None, temperature: float = 0.0) -> ChatOpenAI:
    """Crée une instance LLM via OpenRouter."""
    return ChatOpenAI(
        model=model or "google/gemini-2.5-flash-lite-preview-09-2025",
        temperature=temperature,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )


def get_context_value(
    runtime: Runtime[Context], key: str, default: Any = None
) -> Any:
    """Récupère une valeur du context avec fallback."""
    return (runtime.context or {}).get(key, default)


# =============================================================================
# Node 1: RAG Retrieval
# =============================================================================


async def retrieve_requirement(
    state: State, runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Récupère la description du requirement via RAG."""
    try:
        vector_store = get_vector_store()
        top_k = get_context_value(runtime, "rag_top_k", 5)

        query = f"Requirement {state.req_id}"
        docs = vector_store.similarity_search(query, k=top_k)

        if not docs:
            return {
                "errors": state.errors
                + [f"Aucun document trouvé pour le requirement {state.req_id}"]
            }

        rag_context = "\n\n---\n\n".join(doc.page_content for doc in docs)
        requirement_description = docs[0].page_content

        return {
            "rag_context": rag_context,
            "requirement_description": requirement_description,
        }

    except Exception as e:
        return {"errors": state.errors + [f"Erreur RAG: {str(e)}"]}


# =============================================================================
# Node 2: LLM1 - Test Case Generation
# =============================================================================


async def generate_test_cases(
    state: State, runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Génère tous les test cases à couvrir pour le requirement."""
    if state.errors:
        return {}

    try:
        model = get_context_value(
            runtime, "llm1_model", "google/gemini-2.5-flash-lite-preview-09-2025"
        )
        temperature = get_context_value(runtime, "temperature", 0.0)
        llm = get_llm(model, temperature)

        system_prompt = """Tu es un expert en test logiciel et assurance qualité.
Ta tâche est de générer une liste exhaustive de test cases pour un requirement donné.

Pour chaque test case, fournis:
- Un identifiant unique (TC-XXX)
- Une description claire et concise

Réponds UNIQUEMENT avec une liste JSON de test cases au format:
[
    {"id": "TC-001", "description": "Description du test"},
    {"id": "TC-002", "description": "Description du test"},
    ...
]

Sois exhaustif et couvre tous les scénarios possibles:
- Cas nominaux (comportement attendu)
- Cas limites (valeurs aux bornes)
- Cas d'erreur (conditions invalides)
- Transitions d'état (si applicable)
"""

        user_prompt = f"""Génère tous les test cases pour le requirement suivant:

**Requirement ID**: {state.req_id}

**Description du Requirement**:
{state.requirement_description}

**Contexte additionnel (RAG)**:
{state.rag_context}

Génère la liste complète des test cases en JSON.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await llm.ainvoke(messages)
        content = response.content

        import json
        import re

        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            test_cases_raw = json.loads(json_match.group())
            generated_test_cases = [
                f"{tc['id']}: {tc['description']}" for tc in test_cases_raw
            ]
        else:
            generated_test_cases = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and line.strip().startswith("TC-")
            ]

        return {"generated_test_cases": generated_test_cases}

    except Exception as e:
        return {"errors": state.errors + [f"Erreur LLM1: {str(e)}"]}


# =============================================================================
# Node 3: LLM2 - Scenario Analysis
# =============================================================================


async def analyze_test_scenario(
    state: State, runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Analyse le scénario de test et marque les test cases couverts."""
    if state.errors or not state.generated_test_cases:
        return {}

    try:
        model = get_context_value(
            runtime, "llm2_model", "google/gemini-2.5-flash-lite-preview-09-2025"
        )
        temperature = get_context_value(runtime, "temperature", 0.0)
        llm = get_llm(model, temperature)

        system_prompt = """Tu es un expert en analyse de tests logiciels.
Ta tâche est d'analyser un scénario de test XML et de déterminer quels test cases de la liste sont couverts.

Analyse le scénario XML en détail:
- Regarde les étapes du test (TrackUpdates, SystemStatusUpdate, etc.)
- Regarde les résultats attendus (TestResult, Alerts)
- Identifie les conditions testées

Pour chaque test case de la liste, indique s'il est présent (couvert) dans le scénario.

Réponds UNIQUEMENT en JSON au format:
[
    {"id": "TC-001", "description": "Description", "present": true},
    {"id": "TC-002", "description": "Description", "present": false},
    ...
]

present = true signifie que ce cas de test EST vérifié par le scénario XML.
present = false signifie que ce cas de test N'EST PAS vérifié par le scénario XML.
"""

        test_cases_formatted = "\n".join(
            f"- {tc}" for tc in state.generated_test_cases
        )

        user_prompt = f"""Analyse le scénario de test suivant et détermine quels test cases sont couverts.

**Requirement**: {state.req_id}
**Description du Requirement**:
{state.requirement_description[:1000]}

**Liste des Test Cases à vérifier**:
{test_cases_formatted}

**Scénario de Test XML**:
```xml
{state.test_scenario}
```

Pour chaque test case, indique si le scénario le couvre (present: true/false).
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await llm.ainvoke(messages)
        content = response.content

        import json
        import re

        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            test_cases_with_status = json.loads(json_match.group())
        else:
            # Fallback: marquer tous comme non couverts
            test_cases_with_status = []
            for tc in state.generated_test_cases:
                parts = tc.split(":", 1)
                tc_id = parts[0].strip()
                tc_desc = parts[1].strip() if len(parts) > 1 else ""
                test_cases_with_status.append({
                    "id": tc_id,
                    "description": tc_desc,
                    "present": False
                })

        return {"test_cases_with_status": test_cases_with_status}

    except Exception as e:
        return {"errors": state.errors + [f"Erreur LLM2: {str(e)}"]}


# =============================================================================
# Graph Definition
# =============================================================================

graph = (
    StateGraph(State, context_schema=Context, input=StateInput)
    .add_node("retrieve_requirement", retrieve_requirement)
    .add_node("generate_test_cases", generate_test_cases)
    .add_node("analyze_test_scenario", analyze_test_scenario)
    .add_edge("__start__", "retrieve_requirement")
    .add_edge("retrieve_requirement", "generate_test_cases")
    .add_edge("generate_test_cases", "analyze_test_scenario")
    .add_edge("analyze_test_scenario", "__end__")
    .compile(name="Test Coverage Pipeline")
)
