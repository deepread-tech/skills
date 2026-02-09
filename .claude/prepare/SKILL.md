---
name: prepare
description: Session opener. Analyzes a task description and creates a scoped plan with a checklist, affected files, and which skills to run. Use at the start of every coding session before writing any code.
allowed-tools: Bash, Read, Grep, Glob
argument-hint: describe the task (e.g. "add a new pipeline node for classification")
---

# Prepare

You are DeepRead's tech lead. The developer is about to start a task. Your job is to analyze the scope, build a checklist of everything they must not miss, and tell them which skills to run and when.

## Input

The task description: `$ARGUMENTS`

If no arguments provided, ask what the developer is working on.

## Step 1: Classify the Task

Determine which categories apply (can be multiple):

| Category | Signal |
|----------|--------|
| **Pipeline** | New/modified node, tool, graph, state change |
| **API** | New/modified endpoint, request/response model |
| **Database** | New table, column, migration, model change |
| **Service** | New/modified service (auth, storage, billing, AI models) |
| **Feature** | User-facing capability spanning multiple layers |
| **Bug Fix** | Fix to existing behavior |
| **Refactor** | Structural change, no new behavior |
| **Config** | CI/CD, dependencies, environment, Makefile |

## Step 2: Map the Blast Radius

Based on the category, identify every file and layer that will be touched.

**Start with docs — they describe the architecture and file paths:**
- `docs/architecture/overview.md` — directory structure, layer descriptions
- `docs/architecture/pipelines.md` — pipeline node/tool/graph patterns
- `docs/architecture/process-flow.md` — pipeline execution flow
- `AGENTS.md` — code patterns, key file paths, service descriptions
- `docs/api/reference.md` — API endpoints
- `docs/development/migrations.md` — migration process
- `docs/development/testing.md` — test structure

**Only read source code when the docs don't answer something specific** (e.g., checking current state keys in `src/pipelines/state.py`, or seeing what models exist in `src/api/models.py`).

### Pipeline Work
```
src/pipelines/state.py          ← new state keys?
src/pipelines/nodes/             ← new or modified node
src/pipelines/tools/             ← new utility needed?
src/pipelines/graphs/            ← wire node into graph
```

### API Work
```
src/api/models.py               ← request/response models (source of truth)
src/api/v1/routes.py             ← user-facing routes
src/api/dashboard/v1/            ← dashboard routes
src/services/                    ← business logic behind the endpoint
```

### Database Work
```
src/core/models.py               ← SQLAlchemy model
supabase/migrations/             ← migration SQL file
src/api/models.py                ← if field is API-exposed
```

### Service Work
```
src/services/                    ← service implementation
src/core/config.py               ← new env vars?
src/core/exceptions.py           ← new exception types?
```

### Feature (spans layers)
Map each layer it touches using the categories above. Features typically hit API + Service + possibly Database + possibly Pipeline.

## Step 3: Build the Checklist

Create a checklist specific to this task. Include items from ALL relevant categories.

### Always Include
- [ ] Read existing code in the area before writing anything
- [ ] Follow absolute imports (`from src.module import thing`)
- [ ] Full type annotations on all functions
- [ ] `logger = logging.getLogger(__name__)` in new files
- [ ] No bare `except:` — specify exception types
- [ ] No `print()` in `src/`

### If Pipeline
- [ ] Node is `async` with `@traceable(name="...")` decorator
- [ ] Node takes `PipelineState`, returns partial `dict`
- [ ] `step_timings` tracked (start/elapsed/update pattern)
- [ ] New state keys added to `PipelineState` in `state.py`
- [ ] Tools are pure — no LLM calls, no service imports
- [ ] `asyncio.Semaphore` if processing pages in parallel
- [ ] Cost tracking via `cost_tracking.py` for LLM calls
- [ ] Node wired into graph with correct edges

### If API
- [ ] Request/response models in `src/api/models.py`
- [ ] Route follows existing patterns (auth, error handling)
- [ ] Rate limiting applied if user-facing
- [ ] Proper HTTP status codes
- [ ] Response model matches what frontend expects

### If Database
- [ ] SQLAlchemy model updated in `src/core/models.py`
- [ ] Migration file: `supabase/migrations/YYYYMMDDHHMMSS_name.sql`
- [ ] `IF NOT EXISTS` / `IF EXISTS` for idempotency
- [ ] RLS enabled on tables with `user_id`
- [ ] Indexes on foreign keys and query columns
- [ ] `TIMESTAMPTZ` not `TIMESTAMP`
- [ ] `JSONB` not `JSON`

### If Service
- [ ] Service handles its own errors (try/except with logging)
- [ ] External calls have timeouts
- [ ] New env vars added to `src/core/config.py`
- [ ] Service is injectable/mockable for testing

### If Config/CI
- [ ] `make quick-check` still passes
- [ ] CI workflow updated if new test markers or steps needed

### Testing (Always)
- [ ] Unit tests for new functions (mocked dependencies)
- [ ] Integration tests if multi-component interaction
- [ ] Use existing fixtures from `tests/conftest.py`
- [ ] `@pytest.mark.unit` or `@pytest.mark.integration` on every test
- [ ] `@pytest.mark.asyncio` for async tests
- [ ] Tests pass: `uv run pytest <test_file> -v`

### Documentation (Always)
- [ ] Update relevant docs if behavior/architecture changed
- [ ] Update `AGENTS.md` if new patterns introduced

## Step 4: Recommend Skills

Based on the task, recommend which skills to run and when:

| When | Skill | Reason |
|------|-------|--------|
| After coding | `/test-gen <file>` | Generate tests for new code |
| After pipeline work | `/pipeline-check` | Validate node contracts and tool purity |
| After coding | `/enforce` | Catch pattern violations |
| If DB changed | `/migrate` | Create migration properly |
| If API changed | `/sync-repos` | Check cross-repo impact |
| Before commit | `/pre-commit` | Final go/no-go |

Only recommend skills that are relevant to this specific task.

## Output Format

```
## Prepare: [short task title]

### Scope
[1-2 sentence summary of what this task involves]

### Category
[Pipeline / API / Database / Service / Feature / Bug Fix / Refactor]

### Files to Touch
- `path/to/file.py` — what to do here
- `path/to/other.py` — what to do here

### Checklist
- [ ] item 1
- [ ] item 2
- [ ] ...

### Skills to Run
1. After coding → `/test-gen path/to/new_file.py`
2. After coding → `/pipeline-check` (if pipeline)
3. Before commit → `/pre-commit`

### Watch Out For
[Anything tricky or easy to miss for this specific task]
```

## Rules

- **Read docs first, code second.** The `docs/` directory and `AGENTS.md` describe architecture, file paths, and patterns. Only read source code when the docs don't answer something specific. This saves tokens and is faster.
- **Be specific** — reference real file names, real function names, real state keys.
- **Don't over-scope** — only include checklist items relevant to this task.
- **Surface gotchas** — warn about things that are easy to miss for this specific task.
