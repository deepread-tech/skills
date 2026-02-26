# DeepRead Skills

Teach any AI agent how to use the [DeepRead](https://www.deepread.tech) OCR API.

Install these skills and your AI coding assistant instantly knows how to integrate DeepRead — sign up, get an API key, extract text and structured data from documents, use blueprints for optimized accuracy, handle webhooks, and manage errors.

## Skills

| Skill | What it does |
|-------|-------------|
| `/setup` | Get started — signup, API key, first request, structured extraction, blueprints |
| `/api` | Full API reference — all endpoints, auth, schemas, blueprints, webhooks, code examples |
| `/form-fill` | Fill PDF forms — upload any PDF + JSON data, get back a completed PDF with quality report |

## Install

### Claude Code

```bash
npx skills add deepread-tech/skills
```

After installing, use the slash commands:

```
/setup      # walks you through signup, API key, and first request
/api        # full API reference — your agent can write integration code in any language
/form-fill  # fill PDF forms — upload any PDF + JSON data, get back a completed PDF
```

### Cursor

Copy the rule files into your project:

```bash
git clone https://github.com/deepread-tech/skills.git /tmp/deepread-skills
cp -r /tmp/deepread-skills/.cursor .
```

Or manually copy `.cursor/rules/deepread-setup.mdc`, `.cursor/rules/deepread-api.mdc`, and `.cursor/rules/deepread-form-fill.mdc` into your project's `.cursor/rules/` directory.

Rules use `alwaysApply: false` — Cursor will invoke them automatically when you're working with the DeepRead API.

### Windsurf

Copy the rule files into your project:

```bash
git clone https://github.com/deepread-tech/skills.git /tmp/deepread-skills
cp -r /tmp/deepread-skills/.windsurf .
```

Or manually copy `.windsurf/rules/deepread-setup.md`, `.windsurf/rules/deepread-api.md`, and `.windsurf/rules/deepread-form-fill.md` into your project's `.windsurf/rules/` directory.

### Clawhub (OpenClaw Registry)

```bash
clawhub add deepread-tech/deepread-ocr
```

The skills are published to the OpenClaw registry as `user-invocable` commands. Use `/setup`, `/api`, and `/form-fill` after installation.

## What is DeepRead

AI-native OCR API. Upload a PDF or image, get back extracted text and structured data. Multi-model consensus pipelines deliver 97%+ accuracy and flag uncertain fields for human review.

**Key features:**
- Structured extraction via JSON Schema
- Blueprints — optimized reusable schemas with 20-30% accuracy improvement
- Per-field confidence flags (`hil_flag`) for human-in-the-loop review
- Webhook notifications
- Shareable preview links (no auth needed)

**Links:**
- Dashboard: `https://www.deepread.tech/dashboard`
- Docs: `https://www.deepread.tech/docs`

## License

MIT — [DeepRead Technologies](https://www.deepread.tech)
