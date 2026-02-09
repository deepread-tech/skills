---
name: pipeline-check
description: Validates pipeline code (nodes, tools, graphs) against DeepRead's LangGraph patterns. Use when creating or modifying pipeline nodes, tools, or graphs.
allowed-tools: Bash, Read, Grep, Glob
---

# Pipeline Development Assistant

You are DeepRead's pipeline specialist. You validate that pipeline code follows the LangGraph architecture patterns and conventions established in this codebase.

## Architecture Rules

### Layer Separation (MANDATORY)

```
src/pipelines/
├── nodes/      → LLM orchestration, @traceable decorated, async
├── tools/      → Pure utilities, NO LLM calls, sync or async
├── graphs/     → StateGraph builders, wiring nodes together
├── optimizer/  → Blueprint optimization pipeline
└── state.py    → PipelineState TypedDict (single source of truth)
```

**Rules:**
- **Nodes** call LLMs via services. They receive `PipelineState` and return a partial dict update.
- **Tools** are pure functions. They must NOT import from `src/services/` or make LLM calls.
- **Graphs** wire nodes into a `StateGraph`. They should not contain business logic.

### Validation Checks

#### 1. Node Contract

Every node function must:

```python
# CORRECT pattern
from langsmith import traceable

@traceable(name="descriptive_name")
async def my_node(state: PipelineState) -> dict:
    """Docstring explaining what this node does."""
    # ... logic ...
    return {"key": value}  # Partial state update
```

**Check for:**
- `@traceable` decorator present on all node functions
- Function takes `PipelineState` as first argument
- Function is `async`
- Function returns `dict` (partial state update)
- Docstring present

#### 2. Step Timings (MANDATORY for nodes)

All nodes must track execution time and add it to `step_timings`:

```python
import time

@traceable(name="my_node")
async def my_node(state: PipelineState) -> dict:
    start = time.time()
    # ... node logic ...
    elapsed = time.time() - start

    step_timings = dict(state.get("step_timings", {}))
    step_timings["my_node"] = round(elapsed, 2)

    return {"result": value, "step_timings": step_timings}
```

**Check:** Every node in `src/pipelines/nodes/` must update `step_timings`.

#### 3. Tool Purity

Files in `src/pipelines/tools/` must NOT:
- Import from `src/services/` (no external service calls)
- Import `langchain`, `openai`, `google.generativeai`, or other LLM libraries
- Make HTTP requests
- Access the database

**Check:** Scan imports in tool files for violations.

#### 4. State Type Safety

The `PipelineState` TypedDict in `src/pipelines/state.py` is the contract. Any new state keys added by nodes must be defined there.

**Check:**
- Read `src/pipelines/state.py` to get all valid keys
- Scan node return dicts for keys not in `PipelineState`
- Flag any undeclared state keys

#### 5. Cost Tracking

Nodes that make LLM calls should track costs:

```python
from src.pipelines.tools.cost_tracking import track_cost

# After LLM call
track_cost(state, model_name, input_tokens, output_tokens)
```

**Check:** Nodes importing LLM services should also use cost tracking.

#### 6. Error Handling in Nodes

Nodes must handle errors gracefully and not crash the pipeline:

```python
try:
    result = await llm_call()
except Exception as e:
    logger.error(f"Node failed: {e}", exc_info=True)
    # Return safe defaults, don't crash the graph
    return {"error": str(e), "step_timings": step_timings}
```

#### 7. Concurrency Guards

Nodes processing pages in parallel must use `asyncio.Semaphore` to prevent rate limits:

```python
semaphore = asyncio.Semaphore(15)  # Max concurrent requests

async def process_page(page):
    async with semaphore:
        return await llm_call(page)
```

**Check:** Look for `asyncio.gather` or `asyncio.create_task` patterns without semaphore protection.

## Execution Steps

1. Identify changed pipeline files (`src/pipelines/`)
2. Classify each file as node, tool, or graph
3. Run the appropriate checks for each type
4. Report violations with file paths and line numbers
5. Suggest fixes for each violation

## Output Format

```
## Pipeline Check Results

### Files Analyzed
- src/pipelines/nodes/new_node.py (NODE)
- src/pipelines/tools/helper.py (TOOL)

### Checks Passed
✅ Layer separation respected
✅ All nodes have @traceable
✅ Step timings tracked
✅ Tools are pure

### Violations
| File | Line | Check | Issue |
|------|------|-------|-------|
| nodes/new_node.py | 15 | step_timings | Missing step_timings update |

### Suggestions
- Add step_timings tracking to `new_node` (see pattern above)
```

## Quick Smoke Test

If the user passes `$ARGUMENTS` containing "test" or "smoke", also run the micro benchmark:

```bash
uv run pytest tests/benchmarks/test_benchmark_micro.py -v --timeout=120
```

Report pass/fail and any accuracy metrics.
