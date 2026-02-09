# DeepRead Development Skills

Production-grade workflow skills for building high-quality codebases with automated quality checks, testing, and documentation sync.

## About This Repository

This repository contains 8 development workflow skills designed for teams building production applications. These skills automate code quality checks, test generation, database migrations, and cross-repo synchronization.

Each skill is self-contained in its own folder with a `SKILL.md` file containing the instructions and metadata that AI agents use.

## Skill Sets

### Development Workflow Skills

| Skill | Description |
|-------|-------------|
| **prepare** | Session planner - analyzes tasks and creates scoped plans with checklists |
| **enforce** | Code standards validator - catches import, type, and logging violations |
| **test-gen** | Test generator - creates tests following your testing patterns |
| **pipeline-check** | Pipeline validator - validates node contracts and tool purity |
| **migrate** | Database migration helper - creates migrations and updates models |
| **sync-repos** | Cross-repo analyzer - shows which repos need updates after changes |
| **pre-commit** | All-in-one checker - runs all quality checks before committing |
| **doc-sync** | Documentation synchronizer - finds and fixes stale docs |

## Installation

Install all skills with the CLI:

```bash
npx skills add deepread-tech/skills
```

## Usage

After installation, use skills by referencing them:

```bash
# At start of coding session
/prepare "add new feature X"

# After writing code
/enforce
/test-gen

# Before committing
/pre-commit
```

## What These Skills Do

These skills were built for [DeepRead](https://www.deepread.tech) - an AI-native OCR API. We use them daily to:

- Enforce absolute imports, full type annotations, and proper error handling
- Generate tests with proper fixtures and markers
- Validate pipeline nodes follow async/traceable patterns
- Create database migrations with proper RLS and indexes
- Track API changes across our multi-repo architecture
- Keep documentation in sync with code changes

## Typical Workflow

```bash
1. /prepare "task description"   # Plan the work
2. # Write code...
3. /test-gen                      # Generate tests
4. /pre-commit                    # Run all checks
5. git commit                     # Commit when green
```

## Customization

These skills are designed for Python projects with specific patterns, but can be adapted:

- Replace file paths with your project structure
- Adjust code patterns to match your style guide
- Modify architecture references to fit your system

## About DeepRead

[DeepRead](https://www.deepread.tech) is an AI-native OCR API that extracts structured data from documents with 95%+ accuracy. These skills help us maintain code quality across our multi-repo architecture.

## License

MIT - See [LICENSE](./LICENSE)

## Links

- **DeepRead**: https://www.deepread.tech
- **GitHub**: https://github.com/deepread-tech
- **Support**: hello@deepread.tech
