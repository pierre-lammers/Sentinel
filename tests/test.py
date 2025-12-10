import asyncio
from langfuse import get_client
from agent.graph import graph

langfuse = get_client()


async def process_requirements(req_names: list[str]) -> None:
    """Process a list of requirements through the graph with Langfuse tracing."""
    # Create a span using a context manager
    with langfuse.start_as_current_observation(as_type="span", name="process-request") as span:
        # Your processing logic here
        span.update(output="Processing requirements")

        for req_name in req_names:
            # Create a nested generation for each requirement
            with langfuse.start_as_current_observation(
                as_type="generation", name=f"analyze-{req_name}", model="gpt-3.5-turbo"
            ) as generation:
                # Execute the graph
                result = await graph.ainvoke(
                    {"req_name": req_name},
                    config={
                        "configurable": {
                            "llm1_model": "google/gemini-2.5-flash-lite-preview-09-2025",
                            "llm2_model": "google/gemini-2.5-flash-lite-preview-09-2025",
                            "temperature": 0.0,
                            "rag_top_k": 5,
                        }
                    },
                )

                # Update generation with results
                output_summary = {
                    "requirement": req_name,
                    "test_cases_generated": len(result.get("generated_test_cases", [])),
                    "scenarios_analyzed": len(result.get("scenario_results", [])),
                    "aggregated_test_cases": len(result.get("aggregated_test_cases", [])),
                    "errors": result.get("errors", []),
                }
                generation.update(output=output_summary)

    # All spans are automatically closed when exiting their context blocks

    # Flush events in short-lived applications
    langfuse.flush()


if __name__ == "__main__":
    # Array de requirements à analyser
    requirements = ["ARR-044"]

    # Run the async function
    asyncio.run(process_requirements(requirements))