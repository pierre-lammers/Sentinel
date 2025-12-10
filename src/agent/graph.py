"""Pipeline RAG + Multi-LLM pour analyse de couverture de tests.

Ce module définit un graph LangGraph qui:
1. Récupère la description d'un requirement via RAG
2. Génère les test cases à couvrir (LLM1)
3. Analyse un scénario de test et marque les test cases couverts (LLM2)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, cast

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field, SecretStr
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
# Structured Output Models (Pydantic)
# =============================================================================


class GeneratedTestCase(BaseModel):
    """Un test case généré par le LLM."""

    id: str = Field(description="Identifiant unique du test case (ex: TC-001)")
    description: str = Field(description="Description claire et concise du test case")


class TestCaseList(BaseModel):
    """Liste de test cases générés pour un requirement."""

    test_cases: List[GeneratedTestCase] = Field(
        description="Liste exhaustive des test cases couvrant tous les scénarios possibles"
    )


class AnalyzedTestCase(BaseModel):
    """Un test case avec son statut de couverture."""

    id: str = Field(description="Identifiant du test case (ex: TC-001)")
    description: str = Field(description="Description du test case")
    present: bool = Field(
        description="True si le test case est couvert par le scénario XML, False sinon"
    )


class TestCaseAnalysis(BaseModel):
    """Résultat de l'analyse de couverture des test cases."""

    test_cases: List[AnalyzedTestCase] = Field(
        description="Liste des test cases avec leur statut de couverture"
    )


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
    )
    return Chroma(
        collection_name="srs_db",
        embedding_function=embeddings,
        persist_directory="./rag_srs_chroma_db",
    )


def get_llm(model: str | None = None, temperature: float = 0.0) -> ChatOpenAI:
    """Crée une instance LLM via OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return ChatOpenAI(
        model=model or "google/gemini-2.5-flash-lite-preview-09-2025",
        temperature=temperature,
        base_url="https://openrouter.ai/api/v1",
        api_key=SecretStr(api_key) if api_key else None,
    )


def get_context_value(runtime: Runtime[Context], key: str, default: Any = None) -> Any:
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
        docs = await vector_store.asimilarity_search(query, k=top_k)

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

        # Utiliser structured output avec le modèle Pydantic
        structured_llm = llm.with_structured_output(TestCaseList)

        system_prompt = """Tu es un expert en test logiciel et assurance qualité.
Ta tâche est de générer une liste exhaustive de test cases pour un requirement donné.

Pour chaque test case, fournis:
- Un identifiant unique (TC-XXX)
- Une description claire et concise

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
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = cast(TestCaseList, await structured_llm.ainvoke(messages))

        generated_test_cases = [
            f"{tc.id}: {tc.description}" for tc in response.test_cases
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

        # Utiliser structured output avec le modèle Pydantic
        structured_llm = llm.with_structured_output(TestCaseAnalysis)

        system_prompt = """Tu es un expert en analyse de tests logiciels.
Ta tâche est d'analyser un scénario de test XML et de déterminer quels test cases de la liste sont couverts.

Analyse le scénario XML en détail:
- Regarde les étapes du test (TrackUpdates, SystemStatusUpdate, etc.)
- Regarde les résultats attendus (TestResult, Alerts)
- Identifie les conditions testées

Pour chaque test case de la liste, indique s'il est présent (couvert) dans le scénario.

present = true signifie que ce cas de test EST vérifié par le scénario XML.
present = false signifie que ce cas de test N'EST PAS vérifié par le scénario XML.
"""

        test_cases_formatted = "\n".join(f"- {tc}" for tc in state.generated_test_cases)

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
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = cast(TestCaseAnalysis, await structured_llm.ainvoke(messages))

        # Convertir les objects Pydantic en TypedDict pour la compatibilité
        test_cases_with_status: List[TestCase] = [
            {"id": tc.id, "description": tc.description, "present": tc.present}
            for tc in response.test_cases
        ]

        return {"test_cases_with_status": test_cases_with_status}

    except Exception as e:
        return {"errors": state.errors + [f"Erreur LLM2: {str(e)}"]}


# =============================================================================
# Graph Definition
# =============================================================================

graph = (
    StateGraph(State, context_schema=Context)
    .add_node("retrieve_requirement", retrieve_requirement)
    .add_node("generate_test_cases", generate_test_cases)
    .add_node("analyze_test_scenario", analyze_test_scenario)
    .add_edge("__start__", "retrieve_requirement")
    .add_edge("retrieve_requirement", "generate_test_cases")
    .add_edge("generate_test_cases", "analyze_test_scenario")
    .add_edge("analyze_test_scenario", "__end__")
    .compile(name="Test Coverage Pipeline")
)
