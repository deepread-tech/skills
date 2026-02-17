# DeepRead Skills

Teach any AI agent how to use the [DeepRead](https://www.deepread.tech) OCR API.

Install these skills and your AI coding assistant instantly knows how to integrate DeepRead — sign up, get an API key, extract text and structured data from documents, use blueprints for optimized accuracy, handle webhooks, and manage errors.

## Skills

| Skill | What it does |
|-------|-------------|
| `/setup` | Get started — signup, API key, first request, structured extraction, blueprints |
| `/api` | Full API reference — all endpoints, auth, schemas, blueprints, webhooks, code examples |

## Install

```bash
npx skills add deepread-tech/skills
```

## Usage

After installing, use the slash commands in Claude Code:

```
/setup    # walks you through signup, API key, and first request
/api      # full API reference — your agent can write integration code in any language
```

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
