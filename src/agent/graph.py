"""Test Coverage Pipeline - LangGraph definition."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    aggregate_test_cases,
    generate_test_cases,
    has_more_scenarios,
    identify_coverage,
    load_current_scenario,
    load_scenarios,
    move_to_next_scenario,
    retrieve_requirement,
    verify_false_positives,
    write_false_positives_report,
)
from agent.state import Context, State

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# =============================================================================
# Graph Definition
# =============================================================================

graph = (
    StateGraph(State, context_schema=Context)
    # Data loading
    .add_node("load_scenarios", load_scenarios)
    .add_node("retrieve_requirement", retrieve_requirement)
    # Test case generation
    .add_node("generate_test_cases", generate_test_cases)
    # Scenario analysis loop
    .add_node("load_current_scenario", load_current_scenario)
    .add_node("identify_coverage", identify_coverage)
    .add_node("verify_false_positives", verify_false_positives)
    .add_node("move_to_next_scenario", move_to_next_scenario)
    # Aggregation
    .add_node("aggregate_test_cases", aggregate_test_cases)
    .add_node("write_false_positives_report", write_false_positives_report)
    # Edges: linear flow
    .add_edge(START, "load_scenarios")
    .add_edge("load_scenarios", "retrieve_requirement")
    .add_edge("retrieve_requirement", "generate_test_cases")
    .add_edge("generate_test_cases", "load_current_scenario")
    # Scenario analysis loop
    .add_edge("load_current_scenario", "identify_coverage")
    .add_edge("identify_coverage", "verify_false_positives")
    .add_edge("verify_false_positives", "move_to_next_scenario")
    .add_conditional_edges(
        "move_to_next_scenario",
        has_more_scenarios,
        {"continue": "load_current_scenario", "end": "aggregate_test_cases"},
    )
    # Final aggregation
    .add_edge("aggregate_test_cases", "write_false_positives_report")
    .add_edge("write_false_positives_report", END)
    .compile(name="Test Coverage Pipeline")
)
