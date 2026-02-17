---
name: api
description: Full DeepRead API reference. All endpoints, auth, request/response formats, blueprints, webhooks, error handling, and code examples.
allowed-tools: Bash, Read, Write
---

# DeepRead API Reference

You are helping a developer integrate DeepRead into their application. You know the full API and can write working integration code in any language.

**Base URL:** `https://api.deepread.tech`
**Auth:** `X-API-Key` header with key from `https://www.deepread.tech/dashboard`

---

## Processing

### POST /v1/process — Submit a Document

Uploads a document for async processing. Returns immediately with a job ID.

**Auth:** `X-API-Key: YOUR_KEY`
**Content-Type:** `multipart/form-data`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | File | Yes | — | PDF, PNG, JPG, or JPEG |
| `pipeline` | string | No | `"standard"` | `"standard"` or `"searchable"` |
| `schema` | string | No | — | JSON Schema for structured extraction |
| `blueprint_id` | string | No | — | Blueprint UUID (mutually exclusive with schema) |
| `include_images` | string | No | `"true"` | Generate preview images and page data |
| `include_pages` | string | No | `"false"` | Per-page breakdown (auto-enabled when include_images=true) |
| `webhook_url` | string | No | — | HTTPS URL to notify on completion |
| `version` | string | No | — | Pipeline version for reproducibility |

**Note:** Provide `schema` OR `blueprint_id`, not both. Without either, only OCR text is returned.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**Errors:**
| Status | Meaning |
|--------|---------|
| 400 | Invalid schema, unsupported file type, both schema and blueprint_id provided |
| 401 | Invalid or missing API key |
| 413 | File exceeds plan limit (15MB free, 50MB paid) |
| 429 | Monthly page quota exceeded or rate limit hit |

---

### GET /v1/jobs/{job_id} — Get Results

Poll until `status` is `completed` or `failed`. Recommended: wait 5s, then poll every 5-10s with exponential backoff, max 5 minutes.

**Auth:** `X-API-Key: YOUR_KEY`

**Response (completed):**
```json
{
  "id": "550e8400-...",
  "status": "completed",
  "created_at": "2025-01-18T10:30:00Z",
  "completed_at": "2025-01-18T10:32:15Z",
  "result": {
    "text": "Full extracted text in markdown",
    "text_preview": "First 500 characters...",
    "text_url": "https://...",
    "data": {
      "vendor": {"value": "Acme Inc", "hil_flag": false, "found_on_page": 1},
      "total": {"value": 1250.00, "hil_flag": true, "reason": "Outside typical range", "found_on_page": 1}
    },
    "pages": [
      {
        "page_number": 1,
        "text": "Page 1 text...",
        "hil_flag": false,
        "review_reason": null,
        "data": {}
      }
    ]
  },
  "metadata": {
    "page_count": 3,
    "pipeline": "standard",
    "review_percentage": 5.0,
    "fields_requiring_review": 1,
    "total_fields": 20,
    "step_timings": {}
  },
  "preview_url": "https://preview.deepread.tech/token123...",
  "webhook_url": "https://yourapp.com/webhook",
  "webhook_delivered": true
}
```

**Notes:**
- `text_url` is provided when full text exceeds 1MB — fetch from this URL instead
- `text_preview` is always the first 500 characters
- `data` is only present if `schema` or `blueprint_id` was provided
- `pages` is present when `include_pages=true` or `include_images=true`
- `preview_url` is a shareable link (no auth needed) to the HIL review interface

**Response (failed):**
```json
{
  "id": "550e8400-...",
  "status": "failed",
  "error": "PDF parsing failed: file may be corrupted"
}
```

**Statuses:** `queued` → `processing` → `completed` or `failed`

---

### GET /v1/preview/{token} — Public Preview (No Auth)

Returns document preview data. Anyone with the token can view — no API key needed. Use for sharing results with stakeholders.

```json
{
  "file_name": "invoice.pdf",
  "status": "completed",
  "created_at": "2025-01-18T10:30:00Z",
  "pages": [
    {
      "page_number": 1,
      "image_url": "https://...",
      "text": "Page text...",
      "hil_flag": false,
      "data": {}
    }
  ],
  "data": {},
  "metadata": {"page_count": 1, "pipeline": "standard", "review_percentage": 0}
}
```

---

### GET /v1/pipelines — List Pipelines (No Auth)

- **standard** — Multi-model consensus (GPT + Gemini), dual OCR with LLM judge, ~2-3 minutes
- **searchable** — Creates searchable PDF with embedded OCR text layer, ~3-4 minutes

---

## Blueprints & Optimizer

Blueprints are optimized, versioned schemas. The optimizer takes your sample documents + expected values and enhances field descriptions for 20-30% accuracy improvement.

### GET /v1/blueprints/ — List Blueprints

**Auth:** `X-API-Key: YOUR_KEY`

Returns all blueprints with active version and accuracy metrics.

### GET /v1/blueprints/{blueprint_id} — Get Blueprint Details

**Auth:** `X-API-Key: YOUR_KEY`

Returns blueprint with all versions, active version schema, and accuracy metrics.

### POST /v1/optimize — Start Optimization

**Auth:** `X-API-Key: YOUR_KEY`

```json
{
  "name": "utility_invoice",
  "description": "Utility bill extraction",
  "document_type": "invoice",
  "initial_schema": {"type": "object", "properties": {...}},
  "training_documents": ["path1.pdf", "path2.pdf"],
  "ground_truth_data": [{"vendor": "Electric Co", "total": 150.00}, ...],
  "target_accuracy": 95.0,
  "max_iterations": 5,
  "max_cost_usd": 10.0
}
```

- `initial_schema` is optional — auto-generated from ground truth if omitted
- Minimum 2 training documents
- `validation_split` (default 0.3) — fraction held out for validation

**Response:**
```json
{
  "job_id": "...",
  "blueprint_id": "...",
  "status": "pending"
}
```

### POST /v1/optimize/resume — Resume Optimization

Resume a failed job or start a new optimization run for an existing blueprint.

### GET /v1/blueprints/jobs/{job_id} — Optimization Job Status

**Auth:** `X-API-Key: YOUR_KEY`

```json
{
  "status": "running",
  "iteration": 2,
  "baseline_accuracy": 68.0,
  "current_accuracy": 88.0,
  "target_accuracy": 95.0,
  "total_cost": 1.82,
  "max_cost_usd": 10.0
}
```

**Statuses:** `pending` → `initializing` → `running` → `completed`, `failed`, or `cancelled`

### GET /v1/blueprints/jobs/{job_id}/schema — Get Optimized Schema

Returns the optimized JSON schema after optimization completes.

### Using a Blueprint

```bash
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@invoice.pdf" \
  -F "blueprint_id=660e8400-..."
```

---

## Webhooks

Pass `webhook_url` when submitting a document to get notified on completion.

**Payload sent to your URL:**
```json
{
  "event": "job.completed",
  "job_id": "550e8400-...",
  "status": "completed",
  "result": {"text": "...", "data": {}},
  "metadata": {},
  "preview_url": "https://preview.deepread.tech/..."
}
```

**Important:**
- Webhooks are **NOT authenticated** — always fetch the canonical result via `GET /v1/jobs/{job_id}` with your API key
- Must be HTTPS
- Return 2xx to confirm delivery
- Delivery is best-effort — use polling as fallback if webhook not received
- Make your endpoint idempotent (may receive duplicates)

---

## Rate Limits

Every response includes these headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Monthly pages in your plan |
| `X-RateLimit-Remaining` | Pages remaining this cycle |
| `X-RateLimit-Used` | Pages used this cycle |
| `X-RateLimit-Reset` | Unix timestamp when quota resets |

**Plans:**
| Plan | Pages/month | Max file | Rate limit |
|------|-------------|----------|------------|
| Free | 2,000 | 15 MB | 10 req/min |
| Pro ($99/mo) | 50,000 | 50 MB | 100 req/min |
| Enterprise | Custom | 50 MB | 500 req/min |

---

## Error Handling

All errors return:
```json
{"detail": "Human-readable error message"}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request — invalid schema, unsupported file, both schema + blueprint_id |
| 401 | Invalid or missing API key |
| 404 | Job not found |
| 413 | File too large for your plan |
| 429 | Rate limit or monthly quota exceeded |
| 500 | Server error |

**Quota exceeded (429):**
```json
{
  "detail": {
    "error": "page_count_exceeded",
    "message": "Document has 100 pages, exceeds 50-page limit for FREE plan. Upgrade to PRO.",
    "page_count": 100,
    "max_pages": 50,
    "plan": "free"
  }
}
```

**Common failure reasons in jobs:**
- Document issues: corrupted, unreadable, poor scan quality, processing timeout
- Schema issues: invalid JSON Schema, required fields not found
- Plan limits: file too large, too many pages, quota exceeded

---

## Code Examples

### Python

```python
import requests
import time
import json

API_KEY = "sk_live_YOUR_KEY"
BASE = "https://api.deepread.tech"

# Submit document with structured extraction
schema = {
    "type": "object",
    "properties": {
        "vendor": {"type": "string", "description": "Vendor or company name"},
        "total": {"type": "number", "description": "Total amount due"},
        "due_date": {"type": "string", "description": "Payment due date"}
    }
}

with open("invoice.pdf", "rb") as f:
    resp = requests.post(
        f"{BASE}/v1/process",
        headers={"X-API-Key": API_KEY},
        files={"file": f},
        data={"schema": json.dumps(schema)}
    )
job_id = resp.json()["id"]

# Poll with exponential backoff
delay = 5
while True:
    time.sleep(delay)
    result = requests.get(
        f"{BASE}/v1/jobs/{job_id}",
        headers={"X-API-Key": API_KEY}
    ).json()

    if result["status"] in ("completed", "failed"):
        break
    delay = min(delay * 1.5, 30)  # cap at 30s

# Use results
if result["status"] == "completed":
    text = result["result"]["text"]
    data = result["result"].get("data", {})
    for field, info in data.items():
        if info["hil_flag"]:
            print(f"REVIEW: {field} = {info['value']} ({info.get('reason')})")
        else:
            print(f"OK: {field} = {info['value']}")
```

### JavaScript / Node.js

```javascript
import fs from "fs";

const API_KEY = "sk_live_YOUR_KEY";
const BASE = "https://api.deepread.tech";

// Submit document
const form = new FormData();
form.append("file", fs.createReadStream("invoice.pdf"));
form.append("schema", JSON.stringify({
  type: "object",
  properties: {
    vendor: { type: "string", description: "Vendor or company name" },
    total: { type: "number", description: "Total amount due" }
  }
}));

const { id: jobId } = await fetch(`${BASE}/v1/process`, {
  method: "POST",
  headers: { "X-API-Key": API_KEY },
  body: form
}).then(r => r.json());

// Poll with backoff
let delay = 5000;
let result;
do {
  await new Promise(r => setTimeout(r, delay));
  result = await fetch(`${BASE}/v1/jobs/${jobId}`, {
    headers: { "X-API-Key": API_KEY }
  }).then(r => r.json());
  delay = Math.min(delay * 1.5, 30000);
} while (!["completed", "failed"].includes(result.status));

console.log(result);
```

### cURL

```bash
# Submit with schema
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@invoice.pdf" \
  -F 'schema={"type":"object","properties":{"vendor":{"type":"string","description":"Vendor name"},"total":{"type":"number","description":"Total amount"}}}'

# Submit with blueprint
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@invoice.pdf" \
  -F "blueprint_id=660e8400-..."

# Get results
curl https://api.deepread.tech/v1/jobs/JOB_ID \
  -H "X-API-Key: YOUR_KEY"

# List blueprints
curl https://api.deepread.tech/v1/blueprints/ \
  -H "X-API-Key: YOUR_KEY"
```

### Webhook Receiver (Python / Flask)

```python
from flask import Flask, request
import requests

app = Flask(__name__)
API_KEY = "sk_live_YOUR_KEY"

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    payload = request.json
    job_id = payload["job_id"]

    # IMPORTANT: Always fetch canonical result from API (webhooks are not authenticated)
    result = requests.get(
        f"https://api.deepread.tech/v1/jobs/{job_id}",
        headers={"X-API-Key": API_KEY}
    ).json()

    # Process result...
    return "", 200  # Return 2xx to confirm delivery
```

---

## Help the Developer

- **Send a document** → POST /v1/process, show code in their language
- **Structured data** → help write a JSON Schema with descriptive field descriptions
- **Better accuracy** → explain blueprints, help set up optimizer
- **Real-time updates** → set up webhook_url, build receiver endpoint
- **Hitting errors** → check API key, plan limits, file format, schema validity
- **Share results** → use preview_url from response (no auth needed)
- **Large documents** → use text_url instead of text field for docs > 1MB
- **Review workflow** → filter fields by hil_flag, route flagged ones to human review
