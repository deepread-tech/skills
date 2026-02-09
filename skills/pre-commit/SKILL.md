---
name: pre-commit
description: Runs all quality checks before committing. Combines enforce, doc-sync, and sync-repos into a single go/no-go report. Use this before every commit.
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Pre-Commit Check

You are DeepRead's pre-commit gatekeeper. Run all quality checks in sequence and give a clear go/no-go verdict.

## Steps

Run these in order. Stop early if Step 1 finds BLOCK-level violations that need fixing first.

### Step 1: Code Standards (enforce)

Check all changed `.py` files against mandatory patterns:

1. Find changed files:
   ```bash
   git diff --name-only HEAD && git diff --cached --name-only
   ```
   If clean, compare to main: `git diff main --name-only`

2. On each changed `.py` file, check:
   - No relative imports (search for `from \.`)
   - All functions have return type annotations (`->`)
   - No bare `except:` without exception type
   - `logger = logging.getLogger(__name__)` in `src/` files
   - No `print()` in `src/` files
   - All imports at top of file

3. **Fix any violations found** using the Edit tool.

### Step 2: Formatting & Linting

```bash
make quick-check
```

If it fails, fix the issues and re-run.

### Step 3: Documentation Sync (doc-sync)

Check if changed code has corresponding docs that are now stale:

| Code Change | Doc to Check |
|-------------|-------------|
| `src/pipelines/nodes/` | `docs/architecture/pipelines.md` |
| `src/pipelines/graphs/` | `docs/architecture/process-flow.md` |
| `src/api/` | `docs/api/reference.md` |
| `src/core/models.py` | `docs/development/migrations.md` |
| `src/services/` | `AGENTS.md` |
| `.github/workflows/` | `docs/development/ci-cd.md` |
| `Makefile` | `AGENTS.md`, `CLAUDE.md` |

Read each affected doc and flag sections that no longer match the code. Fix straightforward updates directly. Report anything that needs human judgment.

### Step 4: Cross-Repo Impact (sync-repos)

Only if changed files include:
- `src/api/models.py` → portal needs type regeneration
- `src/api/v1/routes.py` or `src/api/dashboard/` → portal + gtm
- `src/services/auth.py` → portal + preview
- `src/core/models.py` → check migration exists

Skip this step if none of those files changed.

### Step 5: Verdict

Summarize everything in this format:

```
## Pre-Commit Report

### Code Standards
✅ Passed / ❌ X violations found (fixed/needs attention)

### Formatting & Linting (make quick-check)
✅ Passed / ❌ Failed

### Documentation
✅ All docs current / ⚠️ X docs updated / ❌ X docs need manual review

### Cross-Repo Impact
✅ No impact / ⚠️ Action needed:
- [ ] portal: run `npm run generate:types`
- [ ] gtm: update API docs

---
**VERDICT: ✅ GOOD TO COMMIT / ❌ FIX REQUIRED**
```
