# DeepRead Development Skills

AI agent skills for building high-quality, production-grade codebases with automated quality checks and workflow guidance.

## Installation

```bash
npx skills add deepread-tech/skills
```

## Available Skills

| Skill | Description | When to use |
|-------|-------------|-------------|
| `/prepare` | Session planner with checklist and affected files | Start of every coding session |
| `/enforce` | Code standards validator (imports, types, logging) | After writing/modifying code |
| `/test-gen` | Test generator following testing patterns | After implementing features |
| `/pipeline-check` | Pipeline validator (nodes, tools, graphs) | After modifying pipeline code |
| `/migrate` | Database migration helper | When adding/modifying DB schema |
| `/sync-repos` | Cross-repo impact analyzer | After API/schema changes |
| `/pre-commit` | All-in-one pre-commit checker | Before every commit |
| `/doc-sync` | Documentation synchronizer | After feature implementation |

## Typical Workflow

```bash
1. /prepare "add feature X"   # Plan the work, get checklist
2. # Write code...
3. /test-gen                   # Generate tests
4. /pre-commit                 # Run all checks
5. git commit                  # Commit when green
```

## Quick Use Cases

- **Changed pipeline code?** → `/pipeline-check`
- **Changed API models?** → `/sync-repos`
- **Need DB migration?** → `/migrate`
- **Docs out of date?** → `/doc-sync`
- **About to commit?** → `/pre-commit`

## What These Skills Enforce

### Code Quality Patterns
- Absolute imports only (no relative imports)
- Full type annotations on all functions
- Proper error handling (no bare `except:`)
- Module-level loggers (no `print()` statements)
- 88-character line length

### Architecture Patterns
- Pipeline nodes: async, traceable, return partial state
- Tools: pure functions, no LLM calls
- Services: proper error handling, timeouts
- Database: RLS, indexes, proper types

### Testing Patterns
- Mocked dependencies for unit tests
- Proper pytest markers (`@pytest.mark.unit`)
- Use existing fixtures
- Coverage for new code

## About DeepRead

These skills were built for [DeepRead](https://www.deepread.tech) - an AI-native OCR API that extracts structured data from documents with 95%+ accuracy. We use these skills daily to maintain code quality across our multi-repo architecture.

## License

MIT - See [LICENSE](./LICENSE)

## Links

- **DeepRead Website**: https://www.deepread.tech
- **DeepRead GitHub**: https://github.com/deepread-tech
- **Support**: hello@deepread.tech
