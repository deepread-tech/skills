# DeepRead Skills

Teach any AI agent how to use the [DeepRead](https://www.deepread.tech) OCR API.

Install these skills and your AI coding assistant instantly knows how to integrate DeepRead — sign up, get an API key, extract text and structured data from documents, fill PDF forms, redact PII, use blueprints for optimized accuracy, handle webhooks, and manage errors.

## Skills

| Skill | What it does |
|-------|-------------|
| `/deepread-setup` | Get started — signup, API key, first request, structured extraction, blueprints |
| `/deepread-api` | Full API reference — all endpoints, auth, schemas, blueprints, webhooks, code examples |
| `/deepread-form-fill` | Fill PDF forms — submit form + JSON data, get back completed PDF with quality report |
| `/deepread-pii` | PII removal (Enterprise plans) — upload documents, detect and redact personal information, download clean files |

## Install

### Claude Code

```bash
npx skills add deepread-tech/skills
```

After installing, use the slash commands:

```
/deepread-setup      # walks you through signup, API key, and first request
/deepread-api        # full API reference — your agent can write integration code in any language
/deepread-form-fill  # fill PDF forms with AI — any PDF, no AcroForm needed
/deepread-pii        # detect and redact PII from documents
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
clawhub install uday390/deepread-ocr
```

The skills are published to the OpenClaw registry as `user-invocable` commands. Use `/deepread-setup`, `/deepread-api`, `/deepread-form-fill`, and `/deepread-pii` after installation.

## What is DeepRead

AI-native document processing API. Upload a PDF or image, get back extracted text and structured data. Two engines: Extract (one OCR pass) and Deep Extract (two OCR passes and an LLM judge). Both flag uncertain fields for human review; accuracy is measured on public benchmarks at deepread.tech/benchmarks.

**Key features:**
- **OCR** — Structured extraction via JSON Schema
- **Form Fill** — AI-powered PDF form filling with visual QA
- **PII Removal** — Detect and redact 14 types of personal information (Enterprise plans)
- Blueprints — optimized reusable schemas
- Per-field review flags (`needs_review` + `review_reason`) for human-in-the-loop review
- Human review in DeepRead — send `reviewer_email` and a person checks and corrects the result
- Webhook notifications
- Shareable preview links (no auth needed)

**Pricing:** Extract $15 and Deep Extract $35 per 1,000 pages; the Free plan includes 2,000 pages a month.

**Links:**
- Dashboard: `https://www.deepread.tech/dashboard`
- Docs: `https://www.deepread.tech/docs`

## License

MIT — [DeepRead Technologies](https://www.deepread.tech)
