"""Test Coverage Pipeline - LangGraph definition."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    aggregate_test_cases,
    analyze_scenario,
    analyze_scenario_agent,
    generate_test_cases,
    load_scenarios,
    retrieve_requirement,
    route_scenario_loop,
)
from agent.state import Context, State

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def build_graph(use_agent: bool = False) -> StateGraph[State, Context]:
    """Build the test coverage pipeline graph.

    Args:
        use_agent: If True, use ReAct agent for analysis. If False, use LLM-only.
    """
    builder: StateGraph[State, Context] = StateGraph(State, context_schema=Context)

    # Nodes
    builder.add_node("load_scenarios", load_scenarios)
    builder.add_node("retrieve_requirement", retrieve_requirement)
    builder.add_node("generate_test_cases", generate_test_cases)

    # Use agent or direct LLM for analysis
    if use_agent:
        builder.add_node("analyze_scenario", analyze_scenario_agent)
    else:
        builder.add_node("analyze_scenario", analyze_scenario)

    builder.add_node("aggregate_test_cases", aggregate_test_cases)

    # Edges: linear initialization
    builder.add_edge(START, "load_scenarios")
    builder.add_edge("load_scenarios", "retrieve_requirement")
    builder.add_edge("retrieve_requirement", "generate_test_cases")
    builder.add_edge("generate_test_cases", "analyze_scenario")

    # Scenario loop with conditional routing
    builder.add_conditional_edges(
        "analyze_scenario",
        route_scenario_loop,
        {"continue": "analyze_scenario", "end": "aggregate_test_cases"},
    )

    builder.add_edge("aggregate_test_cases", END)

    return builder


# Default graph (LLM-only for backward compatibility)
graph = build_graph(use_agent=False).compile(name="Test Coverage Pipeline")

# Agent-based graph for advanced analysis
agent_graph = build_graph(use_agent=True).compile(name="Test Coverage Agent Pipeline")
