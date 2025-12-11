"""Pipeline RAG + Multi-LLM pour analyse de couverture de tests.

Ce module définit un graph LangGraph qui:
1. Récupère la description d'un requirement via RAG
2. Génère les test cases à couvrir (LLM1)
3. Analyse un scénario de test et marque les test cases couverts (LLM2)
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

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

    test_cases: list[GeneratedTestCase] = Field(
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

    test_cases: list[AnalyzedTestCase] = Field(
        description="Liste des test cases avec leur statut de couverture"
    )


class ScenarioResult(TypedDict):
    """Résultat de l'analyse d'un scénario de test."""

    scenario_name: str
    scenario_path: str
    test_cases: list[TestCase]


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

    req_name: str  # Nom du requirement (ex: ARR-044)


@dataclass
class State:
    """État de la pipeline de couverture de tests."""

    # --- Inputs ---
    req_name: str = ""  # Nom du requirement (ex: ARR-044)

    # --- Étape 0: Chargement des scénarios ---
    scenario_paths: list[str] = field(default_factory=list)  # Chemins des fichiers XML
    current_scenario_index: int = 0  # Index du scénario en cours
    current_scenario_content: str = ""  # Contenu XML du scénario actuel
    current_scenario_name: str = ""  # Nom du scénario actuel

    # --- Étape 1: RAG ---
    requirement_description: str = ""
    rag_context: str = ""

    # --- Étape 2: LLM1 - Génération des test cases ---
    generated_test_cases: list[str] = field(default_factory=list)

    # --- Étape 3: LLM2 - Analyse des scénarios (résultats cumulés) ---
    scenario_results: list[ScenarioResult] = field(default_factory=list)

    # --- Étape 4: Agrégation des test cases ---
    aggregated_test_cases: list[TestCase] = field(default_factory=list)

    # --- Metadata ---
    errors: list[str] = field(default_factory=list)


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


def get_llm(
    model: str | None = None,
    temperature: float = 0.0,
    max_completion_tokens: int = 46000,
) -> ChatOpenAI:
    """Crée une instance LLM via OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return ChatOpenAI(
        model=model or "google/gemini-2.5-flash-lite-preview-09-2025",
        temperature=temperature,
        max_completion_tokens=max_completion_tokens,
        base_url="https://openrouter.ai/api/v1",
        api_key=SecretStr(api_key) if api_key else None,
    )


def get_context_value(runtime: Runtime[Context], key: str, default: Any = None) -> Any:
    """Récupère une valeur du context avec fallback."""
    return (runtime.context or {}).get(key, default)


def get_dataset_path() -> Path:
    """Retourne le chemin du dossier dataset."""
    return Path(__file__).parent.parent.parent / "dataset"


async def find_scenario_xml_files(req_name: str) -> list[str]:
    """Trouve tous les fichiers XML de scénarios pour un requirement donné.

    Args:
        req_name: Nom du requirement (ex: ARR-044)

    Returns:
        Liste des chemins absolus vers les fichiers XML de scénarios
    """
    dataset_path = get_dataset_path()
    req_folder = dataset_path / f"TS_{req_name}"

    # Vérifier l'existence du dossier de manière asynchrone
    exists = await asyncio.to_thread(req_folder.exists)
    if not exists:
        return []

    # Chercher les fichiers XML dans les sous-dossiers test_XX (async)
    async def find_files() -> list[str]:
        scenario_files: list[str] = []
        # glob est bloquant, le déplacer dans un thread
        test_dirs = await asyncio.to_thread(lambda: sorted(req_folder.glob("test_*")))
        for test_dir in test_dirs:
            is_dir = await asyncio.to_thread(test_dir.is_dir)
            if is_dir:
                xml_files = await asyncio.to_thread(
                    lambda: list(test_dir.glob("scenario_*.xml"))
                )
                scenario_files.extend(str(f) for f in xml_files)
        return scenario_files

    return await find_files()


# =============================================================================
# Node 0: Load Scenarios
# =============================================================================


async def load_scenarios(
    state: State,
    runtime: Runtime[Context],  # noqa: ARG001
) -> dict[str, Any]:
    """Charge la liste des scénarios XML pour le requirement."""
    scenario_paths = await find_scenario_xml_files(state.req_name)

    if not scenario_paths:
        return {
            "errors": state.errors
            + [f"Aucun scénario trouvé pour le requirement {state.req_name}"]
        }

    return {"scenario_paths": scenario_paths}


# =============================================================================
# Node 1: RAG Retrieval
# =============================================================================


async def retrieve_requirement(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
    """Récupère la description du requirement via RAG."""
    try:
        vector_store = get_vector_store()
        top_k = get_context_value(runtime, "rag_top_k", 1)

        query = f"Requirement {state.req_name}"
        docs = await vector_store.asimilarity_search(query, k=top_k)

        if not docs:
            return {
                "errors": state.errors
                + [f"Aucun document trouvé pour le requirement {state.req_name}"]
            }

        requirement_description = docs[0].page_content

        return {
            "rag_context": requirement_description,
            "requirement_description": requirement_description,
        }

    except Exception as e:
        return {"errors": state.errors + [f"Erreur RAG: {str(e)}"]}


# =============================================================================
# Node 2: LLM1 - Test Case Generation
# =============================================================================


async def generate_test_cases(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
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

**Requirement ID**: {state.req_name}

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
# Node 3: Load Current Scenario
# =============================================================================


async def load_current_scenario(
    state: State,
    runtime: Runtime[Context],  # noqa: ARG001
) -> dict[str, Any]:
    """Charge le contenu du scénario XML actuel."""
    if state.errors or not state.scenario_paths:
        return {}

    if state.current_scenario_index >= len(state.scenario_paths):
        return {}

    scenario_path = state.scenario_paths[state.current_scenario_index]
    scenario_name = Path(scenario_path).stem

    try:
        with open(scenario_path, encoding="utf-8") as f:
            content = f.read()
        return {
            "current_scenario_content": content,
            "current_scenario_name": scenario_name,
        }
    except Exception as e:
        return {"errors": state.errors + [f"Erreur lecture {scenario_path}: {str(e)}"]}


# =============================================================================
# Node 4: LLM2 - Scenario Analysis
# =============================================================================


async def analyze_test_scenario(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
    """Analyse le scénario de test actuel et marque les test cases couverts."""
    if (
        state.errors
        or not state.generated_test_cases
        or not state.current_scenario_content
    ):
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

**Requirement**: {state.req_name}
**Scénario**: {state.current_scenario_name}

**Description du Requirement**:
{state.requirement_description[:1000]}

**Liste des Test Cases à vérifier**:
{test_cases_formatted}

**Scénario de Test XML**:
```xml
{state.current_scenario_content}
```
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = cast(TestCaseAnalysis, await structured_llm.ainvoke(messages))

        # Convertir les objects Pydantic en TypedDict et ajouter aux résultats
        test_cases_with_status: list[TestCase] = [
            {"id": tc.id, "description": tc.description, "present": tc.present}
            for tc in response.test_cases
        ]

        # Créer le résultat pour ce scénario
        scenario_result: ScenarioResult = {
            "scenario_name": state.current_scenario_name,
            "scenario_path": state.scenario_paths[state.current_scenario_index],
            "test_cases": test_cases_with_status,
        }

        # Ajouter aux résultats cumulés
        return {"scenario_results": state.scenario_results + [scenario_result]}

    except Exception as e:
        return {"errors": state.errors + [f"Erreur LLM2: {str(e)}"]}


# =============================================================================
# Node 5: Aggregate Test Cases
# =============================================================================


async def aggregate_test_cases(
    state: State,
    runtime: Runtime[Context],  # noqa: ARG001
) -> dict[str, Any]:
    """Agrège les test cases de tous les scénarios avec OR sur le statut present."""
    if not state.scenario_results:
        return {"aggregated_test_cases": []}

    # Créer un dictionnaire {test_case_id: {description, present}}
    aggregated: dict[str, TestCase] = {}

    for scenario_result in state.scenario_results:
        for test_case in scenario_result["test_cases"]:
            tc_id = test_case["id"]
            if tc_id not in aggregated:
                # Premier scénario pour ce test case
                aggregated[tc_id] = {
                    "id": tc_id,
                    "description": test_case["description"],
                    "present": test_case["present"],
                }
            else:
                # Combiner avec OR: true si SOIT ancien SOIT nouveau est true
                aggregated[tc_id]["present"] = (
                    aggregated[tc_id]["present"] or test_case["present"]
                )

    # Convertir en liste
    aggregated_list = list(aggregated.values())

    return {"aggregated_test_cases": aggregated_list}


# =============================================================================
# Node 6: Move to Next Scenario
# =============================================================================


async def move_to_next_scenario(
    state: State,
    runtime: Runtime[Context],  # noqa: ARG001
) -> dict[str, Any]:
    """Incrémente l'index pour passer au scénario suivant."""
    return {"current_scenario_index": state.current_scenario_index + 1}


# =============================================================================
# Conditional Edge: Check if more scenarios
# =============================================================================


def has_more_scenarios(state: State) -> str:
    """Vérifie s'il reste des scénarios à analyser."""
    if state.errors:
        return "end"
    if state.current_scenario_index < len(state.scenario_paths):
        return "continue"
    return "end"


# =============================================================================
# Graph Definition
# =============================================================================

graph = (
    StateGraph(State, context_schema=Context)
    # Nodes
    .add_node("load_scenarios", load_scenarios)
    .add_node("retrieve_requirement", retrieve_requirement)
    .add_node("generate_test_cases", generate_test_cases)
    .add_node("load_current_scenario", load_current_scenario)
    .add_node("analyze_test_scenario", analyze_test_scenario)
    .add_node("move_to_next_scenario", move_to_next_scenario)
    .add_node("aggregate_test_cases", aggregate_test_cases)
    # Edges
    .add_edge("__start__", "load_scenarios")
    .add_edge("load_scenarios", "retrieve_requirement")
    .add_edge("retrieve_requirement", "generate_test_cases")
    .add_edge("generate_test_cases", "load_current_scenario")
    .add_edge("load_current_scenario", "analyze_test_scenario")
    .add_edge("analyze_test_scenario", "move_to_next_scenario")
    # Loop back or end
    .add_conditional_edges(
        "move_to_next_scenario",
        has_more_scenarios,
        {"continue": "load_current_scenario", "end": "aggregate_test_cases"},
    )
    .add_edge("aggregate_test_cases", "__end__")
    .compile(name="Test Coverage Pipeline")
)
