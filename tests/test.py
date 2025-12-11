import asyncio
from typing import Any

from langfuse.langchain import CallbackHandler

from agent import graph


async def test_arr_044_pipeline_with_langfuse() -> None:
    """Test the full pipeline for requirement ARR-044 with Langfuse tracing."""
    # Initialize Langfuse callback handler
    langfuse_handler = CallbackHandler()

    # Define input for ARR-044
    inputs = {"req_name": "ARR-044"}

    # Invoke the graph with Langfuse callback
    res: Any = await graph.ainvoke(
        inputs,  # type: ignore[arg-type]
        config={"callbacks": [langfuse_handler]},
    )

    # Verify the result
    assert res is not None

    # Le résultat est un objet State (dataclass), pas un dict
    assert hasattr(res, "aggregated_test_cases")
    assert isinstance(res.aggregated_test_cases, list)

    # Verify that errors list is present
    assert hasattr(res, "errors")

    # Verify we got test cases generated
    assert len(res.aggregated_test_cases) > 0, "Expected test cases to be generated"


if __name__ == "__main__":
    asyncio.run(test_arr_044_pipeline_with_langfuse())
