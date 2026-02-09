# DeepRead Development Skills

Production-grade workflow skills for building high-quality codebases with automated quality checks, testing, and documentation sync.

## ⚠️ Important: These Are DeepRead-Specific Skills

These skills are designed for **DeepRead's internal development workflow** and assume:

- Python codebase with FastAPI + LangGraph architecture
- Supabase PostgreSQL database
- Multi-repo structure (service, portal, preview, gtm)
- Specific directory structure (`src/pipelines/`, `src/api/`, `docs/`, etc.)
- Pytest with specific markers and fixtures
- AGENTS.md file documenting your patterns

**Can I still use them?** Yes! But you'll need to adapt them to your project structure. See the [Customization](#customization) section.

## About This Repository

This repository contains 8 development workflow skills designed for the DeepRead team. These skills automate code quality checks, test generation, database migrations, and cross-repo synchronization.

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

These skills were built for [DeepRead](https://www.deepread.tech) - an AI-native OCR API that processes documents using multi-pass LangGraph pipelines.

**DeepRead Architecture:**
- **Backend**: FastAPI service with LangGraph-powered document processing pipelines
- **Database**: Supabase PostgreSQL with RLS policies
- **Frontend**: React + TypeScript dashboard (deep-read-portal)
- **Stack**: Python, LangGraph, GPT-5/Gemini, Supabase

**These skills help us:**
- Enforce absolute imports, full type annotations, and proper error handling
- Generate tests with proper fixtures and pytest markers
- Validate LangGraph pipeline nodes follow async/traceable patterns
- Create Supabase migrations with proper RLS and indexes
- Track API changes across our 4-repo architecture
- Keep documentation in sync with code changes

## Typical Workflow

```bash
1. /prepare "task description"   # Plan the work
2. # Write code...
3. /test-gen                      # Generate tests
4. /pre-commit                    # Run all checks
5. git commit                     # Commit when green
```

## Customization & Adaptation

**To adapt these skills for your project:**

### 1. Fork or Clone This Repo
```bash
git clone https://github.com/deepread-tech/skills
cd skills
```

### 2. Update File Paths
Edit each `skills/*/SKILL.md` file:
- Replace `src/pipelines/` with your pipeline directory
- Replace `src/api/` with your API directory
- Replace `docs/` with your docs location
- Update `AGENTS.md` references to your pattern docs

### 3. Adjust Patterns
Modify to match your:
- **Code style**: Import style, type annotations, logging patterns
- **Testing**: Test structure, markers, fixtures
- **Database**: Replace Supabase-specific migrations with your DB tool
- **Architecture**: Replace LangGraph references with your framework

### 4. Remove Unused Skills
If you're not using:
- **pipeline-check**: Remove if not using LangGraph
- **sync-repos**: Remove if single-repo project
- **migrate**: Remove if not using Supabase

### 5. Install Locally
```bash
npx skills add file:///path/to/your/fork
```

**Example Adaptations:**
- **Django project**: Change `src/` → `myapp/`, update DB migration patterns
- **Single repo**: Remove sync-repos skill
- **JavaScript**: Adapt enforce skill for ESLint rules, adjust test-gen for Jest
- **Different DB**: Update migrate skill for Alembic/Django/Prisma

## About DeepRead

[DeepRead](https://www.deepread.tech) is an AI-native OCR API that extracts structured data from documents with 95%+ accuracy. These skills help us maintain code quality across our multi-repo architecture.

## License

MIT - See [LICENSE](./LICENSE)

## Links

- **DeepRead**: https://www.deepread.tech
- **GitHub**: https://github.com/deepread-tech
- **Support**: hello@deepread.tech
