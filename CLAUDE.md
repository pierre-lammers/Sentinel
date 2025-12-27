# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sentinel is a LangGraph agent template that provides a starter project for building agentic workflows. The application is designed to be extended with custom logic while providing integration with LangGraph Server and LangGraph Studio for visualization and debugging.

### Key Technologies

- **LangGraph**: Orchestration framework for building agentic workflows
- **LangGraph Server**: Runtime for deploying and serving LangGraph applications
- **LangGraph Studio**: Visual debugging IDE for agentic applications
- **Python**: 3.10+
- **UV**: Package manager for dependency management

## Project Structure

```
src/agent/
├── graph.py           # Core application logic defining the StatGraph
└── __init__.py        # Public exports

tests/
├── unit_tests/        # Unit tests for graph logic
├── integration_tests/ # Integration tests using actual graph execution
└── conftest.py        # Pytest configuration and fixtures
```

## Core Architecture

The application uses LangGraph's state machine pattern:

1. **State** (`src/agent/graph.py`): Defines the input structure of data flowing through the graph. Extend with fields needed for your application.

2. **Context** (`src/agent/graph.py`): Runtime configuration parameters that can be set per assistant or per invocation. Allows dynamic behavior modification without changing graph definition.

3. **Graph** (`src/agent/graph.py`): The state machine itself, defined using `StateGraph`. Currently a single-node graph with `call_model` that processes state.

The graph is compiled and exposed as the `graph` export, which LangGraph Server uses to run the application.

### Configuration

Graph configuration is specified in `langgraph.json`:
- `graphs.agent`: Points to `src/agent/graph.py:graph` (the entry point)
- `dependencies`: Project package at "."
- `env`: Environment variables loaded from `.env`

## Development Commands

Build and dependency management:
```bash
pip install -e . "langgraph-cli[inmem]"  # Install project + LangGraph CLI
```

Testing:
```bash
make test                          # Run unit tests
make test TEST_FILE=path/to/test   # Run specific test file
make test_watch                    # Run tests in watch mode with hot reload
make integration_tests             # Run integration tests
```

Linting and formatting:
```bash
make format                        # Format Python code
make lint                          # Check code style, types, and imports
make codespell                     # Check code spelling errors
```

Running the application:
```bash
langgraph dev                      # Start development server with hot reload
```

This starts LangGraph Server locally and opens LangGraph Studio at `http://localhost:8000`, where you can visualize the graph, test different inputs, and debug by editing state at any step.

## Development Workflow

1. **Edit the graph** in `src/agent/graph.py`:
   - Modify the `State` class to adjust input structure
   - Modify the `Context` TypedDict to add new configuration parameters
   - Add new nodes with async functions that take `(state: State, runtime: Runtime[Context])` and return a dict
   - Add edges to connect nodes using `add_edge()`

2. **Start the server**: Run `langgraph dev` to begin development

3. **Debug in LangGraph Studio**:
   - Visit `http://localhost:8000`
   - Test with different inputs
   - Edit state at any point in execution and rerun from that step
   - Use the `+` button to start a new thread without previous history

4. **Hot reload**: Local changes are automatically applied

5. **Run tests**: Use `make test` or `make test_watch` to validate behavior

## Key Patterns

### Async Node Functions

Nodes must be async functions that accept the state and runtime context:

```python
async def node_name(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    # Access configuration from runtime.context
    config_param = (runtime.context or {}).get('my_configurable_param')

    # Process state and return updates
    return {"field_name": "new_value"}
```

### Extending with LLM Calls

To add LLM integration:
1. Add LLM provider dependencies (e.g., `langchain-openai`)
2. Create nodes that use LLM providers from LangChain
3. Use environment variables (in `.env`) for API keys
4. Add appropriate context configuration for model selection or system prompts

### Error Handling

Structure nodes to handle errors gracefully:
- Return error information in state updates
- Add conditional edges that route based on error conditions
- Use LangSmith integration (add `LANGSMITH_API_KEY` to `.env`) for tracing and debugging failures

## Testing

Tests are organized as:
- **Unit tests** (`tests/unit_tests/`): Test graph construction and node logic
- **Integration tests** (`tests/integration_tests/`): Test full graph execution with inputs and verify outputs

Use `pytest` fixtures defined in `conftest.py`. The `anyio_backend` fixture ensures async tests use asyncio.

## Environment Variables

Create a `.env` file (copy from `.env.example`) to configure:
- `LANGSMITH_PROJECT`: Name for LangSmith traces
- `LANGSMITH_API_KEY`: API key for LangSmith tracing (optional, for detailed debugging)
- Any LLM provider API keys (e.g., `OPENAI_API_KEY`)

## Deployment

The project is configured to deploy using LangGraph Cloud. The `langgraph.json` specifies:
- Which graph to serve (`agent` graph from `src/agent/graph.py`)
- Environment configuration
- Container image distribution (`wolfi`)

See LangGraph documentation for cloud deployment details.

## Code conventions

When writing code, adhere to the repository's conventions and refer to the MCP LangChain documentation.
Ensure that the lint with ruff and mypy are correct.

### Linting Requirements

After any code changes, **ALWAYS** verify that all linting tools pass:

```bash
make lint       # Runs both ruff and mypy checks
make codespell  # Runs codespell to check for spelling errors
```

This should output no errors before considering a task complete. If there are linting errors:
1. Fix them immediately
2. Re-run `make lint` and `make codespell` to confirm all errors are resolved
3. Only then mark the task as done

**Important**: Before committing or creating a pull request, always run both `make lint` and `make codespell` to ensure code quality and spelling correctness.

## Documentation

### Generate PDF from Markdown

```bash
cd dataset && pandoc SRS.md -o SRS.pdf --pdf-engine=xelatex
```