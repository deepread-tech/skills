---
name: setup
description: Get started with DeepRead. Walks through signup, API key, first request, structured extraction, and blueprints.
allowed-tools: Bash, Read, Write
---

# Setup DeepRead

You are helping a developer get started with DeepRead — an AI-native OCR API that extracts text and structured data from documents (PDFs, images) with 95%+ accuracy.

You submit a file, get a job ID, poll for results. Low-confidence fields are flagged for human review instead of guessing wrong.

**API:** `https://api.deepread.tech`
**Dashboard:** `https://www.deepread.tech`
**Docs:** `https://www.deepread.tech/docs`

---

## Step 1: Sign Up

Go to `https://www.deepread.tech/auth` — sign up with email, GitHub, or Google.

## Step 2: Get an API Key

1. Go to `https://www.deepread.tech/dashboard`
2. Click **"Create New Key"**
3. Name it, pick environment (`development` / `test` / `production`)
4. **Copy immediately** — only shown once

## Step 3: Send Your First Document

```bash
# Submit
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@document.pdf"
# Response: {"id": "550e8400-...", "status": "queued"}

# Poll for results (wait 5s, then every 5-10s)
curl https://api.deepread.tech/v1/jobs/550e8400-... \
  -H "X-API-Key: YOUR_KEY"
# → {"status": "completed", "result": {"text": "extracted text..."}, "preview_url": "..."}
```

Supports PDF, PNG, JPG, JPEG. Max 15MB (free) / 50MB (paid).

## Step 4: Extract Structured Data

Add a `schema` parameter with a JSON Schema. Field descriptions guide the AI — the better the description, the better the extraction.

```bash
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@invoice.pdf" \
  -F 'schema={
    "type": "object",
    "properties": {
      "vendor": {"type": "string", "description": "Company or vendor name on the invoice"},
      "total": {"type": "number", "description": "Total amount due in dollars"},
      "due_date": {"type": "string", "description": "Payment due date"}
    }
  }'
```

Each extracted field comes with quality metadata:

```json
{
  "vendor": {"value": "Acme Inc", "hil_flag": false, "found_on_page": 1},
  "due_date": {"value": "2025-03-15", "hil_flag": true, "reason": "Multiple dates found", "found_on_page": 1}
}
```

- `hil_flag: false` → extracted confidently, safe to auto-accept
- `hil_flag: true` → needs human review — check `reason` for why

## Step 5: Blueprints (Better Accuracy)

Blueprints are optimized schemas that improve accuracy by 20-30%. You give DeepRead sample documents + expected values, it enhances field descriptions automatically.

1. Go to `https://www.deepread.tech/dashboard/optimizer`
2. Upload 4+ sample docs + ground truth JSON
3. DeepRead runs 3-5 optimization iterations
4. Use the optimized blueprint:

```bash
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@invoice.pdf" \
  -F "blueprint_id=YOUR_BLUEPRINT_ID"
```

Use `schema` OR `blueprint_id`, not both.

## Plans

| Plan | Pages/month | Max file | Price |
|------|-------------|----------|-------|
| Free | 2,000 | 15 MB | $0 |
| Pro | 50,000 | 50 MB | $99/mo |
| Enterprise | Custom | 50 MB | Custom |

## What's Next

Use `/api` for the full reference — all endpoints, webhooks, error handling, blueprints API, and code examples in Python, JavaScript, and cURL.

## Help the Developer

- No account yet → walk through signup above
- Has API key → help send first request
- Wants structured data → help write a JSON Schema with good field descriptions
- Wants better accuracy → explain blueprints and optimizer
- Wants full integration → use `/api` for complete reference
