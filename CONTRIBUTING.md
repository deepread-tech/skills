# Contributing to DeepRead Skills

Thanks for your interest in contributing! These skills are designed to be adaptable and we welcome improvements.

## How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-skill-name`
3. **Make your changes**: Add or modify skills in `.claude/skills/`
4. **Test locally**: Install locally with `npx skills add file:///path/to/your/fork`
5. **Submit a PR**: Include a clear description of what your skill does

## Skill Guidelines

Each skill should:
- Have clear, specific use case (when to use it)
- Follow the YAML frontmatter format with `name`, `description`, `allowed-tools`
- Include concrete examples in the markdown content
- Be self-contained (no dependencies on DeepRead-specific code if possible)

## Making Skills Generic

If you want to adapt these skills for your project:
- Replace DeepRead-specific file paths with your own
- Adjust code patterns to match your style guide
- Modify architecture references (pipeline, API structure, etc.)

## Questions?

Open an issue or contact hello@deepread.tech
