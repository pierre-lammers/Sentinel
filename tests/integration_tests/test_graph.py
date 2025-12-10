from typing import Any

import pytest  # type: ignore[import-not-found]

from agent import graph

pytestmark = pytest.mark.anyio


@pytest.mark.langsmith  # type: ignore[untyped-decorator]
async def test_agent_simple_passthrough() -> None:
    inputs = {"req_id": "REQ-001", "test_scenario": "<scenario/>"}
    res: Any = await graph.ainvoke(inputs)  # type: ignore[arg-type]
    assert res is not None
