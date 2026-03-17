# DeepRead Skills

Teach any AI agent how to use the [DeepRead](https://www.deepread.tech) OCR API.

Install these skills and your AI coding assistant instantly knows how to integrate DeepRead — sign up, get an API key, extract text and structured data from documents, fill PDF forms, redact PII, use blueprints for optimized accuracy, handle webhooks, and manage errors.

## Skills

| Skill | What it does |
|-------|-------------|
| `/setup` | Get started — signup, API key, first request, structured extraction, blueprints |
| `/api` | Full API reference — all endpoints, auth, schemas, blueprints, webhooks, code examples |
| `/form-fill` | Fill PDF forms — submit form + JSON data, get back completed PDF with quality report |
| `/pii-removal` | PII removal — upload documents, detect and redact personal information, download clean files |

## Install

### Claude Code

```bash
npx skills add deepread-tech/skills
```

After installing, use the slash commands:

```
/setup      # walks you through signup, API key, and first request
/api        # full API reference — your agent can write integration code in any language
/form-fill      # fill PDF forms with AI — any PDF, no AcroForm needed
/pii-removal   # detect and redact PII from documents
```

### Cursor

Copy the rule files into your project:

```bash
git clone https://github.com/deepread-tech/skills.git /tmp/deepread-skills
cp -r /tmp/deepread-skills/.cursor .
```

Or manually copy `.cursor/rules/deepread-setup.mdc`, `.cursor/rules/deepread-api.mdc`, `.cursor/rules/deepread-form-fill.mdc`, and `.cursor/rules/deepread-pii-removal.mdc` into your project's `.cursor/rules/` directory.

Rules use `alwaysApply: false` — Cursor will invoke them automatically when you're working with the DeepRead API.

### Windsurf

Copy the rule files into your project:

```bash
git clone https://github.com/deepread-tech/skills.git /tmp/deepread-skills
cp -r /tmp/deepread-skills/.windsurf .
```

Or manually copy `.windsurf/rules/deepread-setup.md`, `.windsurf/rules/deepread-api.md`, `.windsurf/rules/deepread-form-fill.md`, and `.windsurf/rules/deepread-pii-removal.md` into your project's `.windsurf/rules/` directory.

### Clawhub (OpenClaw Registry)

```bash
clawhub add deepread-tech/deepread-ocr
```

The skills are published to the OpenClaw registry as `user-invocable` commands. Use `/setup`, `/api`, `/form-fill`, and `/pii-removal` after installation.

## What is DeepRead

AI-native document processing API. Upload a PDF or image, get back extracted text and structured data. Multi-model consensus pipelines deliver 97%+ accuracy and flag uncertain fields for human review.

**Key features:**
- **OCR** — Structured extraction via JSON Schema with 97%+ accuracy
- **Form Fill** — AI-powered PDF form filling with visual QA
- **PII Removal** — Detect and redact 14 types of personal information
- Blueprints — optimized reusable schemas with 20-30% accuracy improvement
- Per-field confidence flags (`hil_flag`) for human-in-the-loop review
- Webhook notifications
- Shareable preview links (no auth needed)

**Links:**
- Dashboard: `https://www.deepread.tech/dashboard`
- Docs: `https://www.deepread.tech/docs`

## License

MIT — [DeepRead Technologies](https://www.deepread.tech)
