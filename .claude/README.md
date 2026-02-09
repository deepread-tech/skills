# Claude Code Skills

Type these as slash commands in Claude Code.

| Skill | When to use it |
|-------|---------------|
| `/prepare` | **Start here.** Analyzes your task and builds a checklist + skill plan. |
| `/pre-commit` | Before committing. Runs all checks and gives you a go/no-go. |
| `/enforce` | After writing code. Catches pattern violations (imports, types, logging). |
| `/test-gen` | After implementing something. Generates tests that follow our patterns. |
| `/pipeline-check` | After touching `src/pipelines/`. Validates node contracts and tool purity. |
| `/migrate` | When you need a DB change. Creates migration + updates SQLAlchemy model. |
| `/sync-repos` | After changing API models or schema. Shows which repos need updates. |
| `/doc-sync` | After a feature ships. Finds stale docs and fixes them. |

## Typical workflow

```
1. /prepare "add X"   ← plan the work
2. Write code
3. /test-gen           ← generate tests
4. /pre-commit         ← check everything
5. git commit
```

## Quick singles

- Changed a pipeline node? → `/pipeline-check`
- Changed `src/api/models.py`? → `/sync-repos`
- Need a new DB table? → `/migrate`
- Docs feel stale? → `/doc-sync`
