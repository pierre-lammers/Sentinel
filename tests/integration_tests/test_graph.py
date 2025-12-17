from typing import Any

import pytest

from agent import graph

pytestmark = pytest.mark.anyio


@pytest.mark.langsmith
async def test_agent_simple_passthrough() -> None:
    inputs = {"req_name": "REQ-001"}
    res: Any = await graph.ainvoke(inputs)  # type: ignore[arg-type]
    assert res is not None
    assert "aggregated_test_cases" in res
    assert "false_positives" in res
