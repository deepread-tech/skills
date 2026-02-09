---
name: test-gen
description: Generates tests for new or modified code following DeepRead's testing patterns. Use after implementing a feature or fixing a bug.
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
argument-hint: file path or description of what to test
---

# Test Generator

You are DeepRead's test generator. You create tests that follow the team's exact patterns and conventions.

## Input

The user will provide either:
- A file path to generate tests for: `$ARGUMENTS`
- A description of what was changed (infer files from context)

If no arguments, detect changed files:
```bash
git diff --name-only HEAD && git diff --cached --name-only
```

## Test Structure

```
tests/
├── unit/           # Fast (<1s), isolated, mocked — DEFAULT
├── integration/    # Multi-component, real DB
├── benchmarks/     # Accuracy validation (don't generate these)
└── optimizer/      # Optimizer pipeline tests
```

**Default to unit tests** unless the user asks for integration tests.

## Step 1: Analyze the Code

Read the source file(s) and identify:
- Public functions/methods to test
- Edge cases (empty input, None, errors)
- Dependencies to mock (services, DB, external APIs)
- Return types and expected shapes

## Step 2: Determine Test Location

Mirror the source path:
- `src/api/v1/routes.py` → `tests/unit/api/v1/test_routes.py`
- `src/pipelines/nodes/ocr.py` → `tests/unit/pipelines/nodes/test_ocr.py`
- `src/services/auth.py` → `tests/unit/services/test_auth.py`

If the test file exists, **add to it**. Don't create a duplicate.

## Step 3: Generate Tests

Follow these exact patterns:

### Unit Test Template

```python
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.module.under_test import function_to_test

logger = logging.getLogger(__name__)


class TestFunctionToTest:
    """Tests for function_to_test."""

    @pytest.mark.unit
    def test_basic_behavior(self):
        """Test the happy path."""
        result = function_to_test(valid_input)
        assert result == expected_output

    @pytest.mark.unit
    def test_edge_case(self):
        """Test with edge case input."""
        result = function_to_test(edge_input)
        assert result == edge_expected

    @pytest.mark.unit
    def test_error_handling(self):
        """Test that errors are handled correctly."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

### Async Test Template (for pipeline nodes/services)

```python
import pytest

from src.pipelines.nodes.my_node import my_node


class TestMyNode:
    """Tests for my_node."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """Test node executes and returns expected state update."""
        state = {
            "job_id": "test-job",
            "images": [b"fake_image"],
            "step_timings": {},
        }
        result = await my_node(state)
        assert "step_timings" in result
        assert "my_node" in result["step_timings"]
```

### API Route Test Template

```python
import pytest
from fastapi.testclient import TestClient

from src.app import app


class TestMyEndpoint:
    """Tests for /v1/my-endpoint."""

    @pytest.mark.unit
    def test_success(self, authenticated_client):
        """Test successful request."""
        response = authenticated_client.post(
            "/v1/my-endpoint",
            json={"key": "value"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data

    @pytest.mark.unit
    def test_unauthorized(self):
        """Test request without auth fails."""
        client = TestClient(app)
        response = client.post("/v1/my-endpoint")
        assert response.status_code in (401, 403)
```

## Conventions (MANDATORY)

1. **Markers**: Every test must have `@pytest.mark.unit` or `@pytest.mark.integration`
2. **Async tests**: Use `@pytest.mark.asyncio` for async functions
3. **Imports**: Absolute only (`from src.module import thing`)
4. **Imports at top**: All imports at the top of the file
5. **Mocking**: Use `unittest.mock` — mock at the point of use, not definition
   ```python
   # CORRECT — mock where it's imported
   @patch("src.pipelines.nodes.ocr.get_multimodal_model")

   # WRONG — mock at definition
   @patch("src.services.models.get_multimodal_model")
   ```
6. **Class grouping**: Group tests by function/class under test
7. **Docstrings**: Every test method gets a one-line docstring
8. **No print()**: Use `logger` if you need debug output
9. **Fixtures**: Use existing fixtures from `tests/conftest.py`:
   - `mock_auth_service` — bypasses Supabase auth
   - `authenticated_client` — TestClient with auth override
   - `db_session` — in-memory SQLite

## Step 4: Verify Tests Run

After generating tests, run them:

```bash
uv run pytest <test_file> -v --timeout=30
```

If tests fail, fix them. Tests must pass before you're done.

## Output Format

```
## Tests Generated

### Source: src/pipelines/nodes/new_node.py
### Test File: tests/unit/pipelines/nodes/test_new_node.py

| Test | What it covers |
|------|---------------|
| test_basic_execution | Happy path with valid state |
| test_empty_images | Edge case: no images in state |
| test_llm_failure | Error handling when LLM call fails |
| test_step_timings_tracked | Verifies step_timings updated |

### Run Result
✅ 4 passed in 0.3s
```
