---
name: form-fill
description: AI-powered PDF form filling API. Upload any PDF form + your data as JSON — AI detects fields, maps data, fills the form with quality checks, returns a completed PDF. Works with scanned forms, no AcroForm required.
allowed-tools: Bash, Read, Write
user-invocable: true
---

# DeepRead Form Fill

You are helping a developer fill PDF forms using DeepRead's AI-powered form fill API. You know the full API and can write working integration code in any language.

**Base URL:** `https://api.deepread.tech`
**Auth:** `X-API-Key` header with key from `https://www.deepread.tech/dashboard` or via the device authorization flow (use `/setup`)

---

## What Form Fill Does

The developer provides:
1. A blank PDF form (any PDF — scanned, government, custom template)
2. Their data as JSON (e.g. `{"full_name": "Jane Doe", "dob": "1990-03-15"}`)

DeepRead returns:
- A filled PDF with data placed in the correct fields
- A quality report showing what was filled, verified, and what needs human review

**No field mapping, no coordinates, no configuration.** The AI figures out where everything goes using visual coordinate-based filling — not AcroForm fields.

---

## Prerequisites

You need a `DEEPREAD_API_KEY`. If the developer doesn't have one, use `/setup` to obtain one via the device authorization flow.

---

## API Endpoints

### POST /v1/form-fill — Submit a Form for Filling

Uploads a PDF form + JSON data for async processing. Returns immediately with a job ID.

**Auth:** `X-API-Key: YOUR_KEY`
**Content-Type:** `multipart/form-data`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | PDF form to fill |
| `form_fields` | JSON string | Yes | `{"field_name": "value"}` — your data to fill into the form |
| `webhook_url` | string | No | HTTPS URL to receive results when done |
| `idempotency_key` | string | No | Prevent duplicate submissions (same key = same job) |
| `url_expires_in` | integer | No | Signed URL expiry in seconds (default: 604800 = 7 days, min: 3600, max: 604800) |

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
| 400 | Only PDF files are supported, or invalid JSON in form_fields |
| 401 | Invalid or missing API key |
| 429 | Monthly page quota exceeded or rate limit hit |

---

### GET /v1/form-fill/{job_id} — Get Results

Poll until `status` is `completed` or `failed`. Recommended: poll every 5-10 seconds, processing takes 15-30 seconds.

**Auth:** `X-API-Key: YOUR_KEY`
**Rate limit:** 20 requests per 60 seconds

**Response (completed):**
```json
{
  "id": "550e8400-...",
  "status": "completed",
  "file_name": "tax_form.pdf",
  "created_at": "2025-06-15T10:00:00Z",
  "completed_at": "2025-06-15T10:00:18Z",
  "filled_form_url": "https://storage.deepread.tech/form_fill/.../filled.pdf",
  "fields_detected": 25,
  "fields_filled": 23,
  "fields_verified": 21,
  "fields_hil_flagged": 2,
  "duration_seconds": 18.3,
  "report": {
    "summary": {
      "fields_detected": 25,
      "fields_filled": 23,
      "fields_verified": 21,
      "fields_hil_flagged": 2,
      "mappings_created": 23,
      "unmapped_keys": 0,
      "adjustments_made": 3
    },
    "fields": [
      {
        "field_index": 0,
        "label": "Taxpayer Name",
        "field_type": "text",
        "page": 1,
        "value": "Jane Doe",
        "hil_flag": false,
        "verified": true
      },
      {
        "field_index": 8,
        "label": "Total Income",
        "field_type": "text",
        "page": 2,
        "value": "85000",
        "hil_flag": true,
        "verified": false,
        "reason": "Text overlaps adjacent field"
      }
    ],
    "mappings": [
      {
        "user_key": "taxpayer_name",
        "field_index": 0,
        "value_to_fill": "Jane Doe",
        "confidence": 0.95
      }
    ],
    "unmapped_user_keys": [],
    "adjustments_made": ["Field 8: reduced font size from 12pt to 8pt"],
    "qa_feedback": ["Total Income: text overlaps adjacent field"],
    "errors": []
  },
  "errors": null,
  "error_message": null
}
```

**Response (failed):**
```json
{
  "id": "550e8400-...",
  "status": "failed",
  "error_message": "Form fill timed out after 600s"
}
```

**Statuses:** `queued` → `processing` → `completed` or `failed`

---

## Report Details

### Fields Summary

| Metric | Meaning |
|--------|---------|
| `fields_detected` | Total form fields AI found on the PDF |
| `fields_filled` | Fields where your data was placed |
| `fields_verified` | Fields that passed visual QA (text readable, positioned correctly) |
| `fields_hil_flagged` | Fields needing human review (AI couldn't fully verify) |

Typical result: 90-95% of fields verified, 2-5% flagged for review.

### HIL Flags (Human-in-the-Loop)

A field gets `hil_flag: true` when:
- Text overlaps an adjacent field
- Font had to be shrunk significantly
- Value doesn't visually match field expectations
- Repair attempts didn't fully resolve the issue

Each flagged field includes a `reason` explaining why review is needed.

### Unmapped Keys

If your JSON has keys that don't match any form field, they appear in `unmapped_user_keys`. This means the form doesn't have a matching field, or the field label is ambiguous.

---

## Webhooks

Pass `webhook_url` when submitting a form to get notified on completion.

**Completed payload:**
```json
{
  "job_id": "550e8400-...",
  "status": "completed",
  "created_at": "2025-06-15T10:00:00Z",
  "completed_at": "2025-06-15T10:00:18Z",
  "result": {
    "filled_form_url": "https://storage.deepread.tech/form_fill/.../filled.pdf",
    "fields_detected": 25,
    "fields_filled": 23,
    "fields_verified": 21,
    "fields_hil_flagged": 2,
    "report": { }
  }
}
```

**Failed payload:**
```json
{
  "job_id": "550e8400-...",
  "status": "failed",
  "created_at": "2025-06-15T10:00:00Z",
  "completed_at": "2025-06-15T10:00:18Z",
  "error": "Form fill timed out after 600s",
  "errors": ["Form fill timed out after 600s"]
}
```

**Important:**
- Webhooks are **NOT authenticated** — always fetch the canonical result via `GET /v1/form-fill/{job_id}` with your API key
- Must be HTTPS
- Return 2xx to confirm delivery
- Make your endpoint idempotent (may receive duplicates)

---

## How It Works

```
Upload PDF + JSON data
       │
       ▼
┌──────────────────────┐
│ 1. DETECT FIELDS     │  Vision AI scans every page, finds all fillable areas
│    (visual, not PDF   │  Returns: label, type, page, bounding box coordinates
│     form fields)      │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 2. MAP DATA          │  AI semantically matches your JSON keys → form fields
│    "full_name" →     │  Transforms values: splits names, formats dates,
│    "Full Name" field  │  converts checkboxes, adds currency symbols
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 3. FILL FORM         │  Places text at visual coordinates on the PDF
│    coordinate-based   │  Handles: text, checkboxes, dropdowns
│    insertion          │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 4. QA CHECK          │  Vision AI re-reads the filled form to verify:
│    visual verify      │  - Text is readable, not cut off
│                       │  - Positioned correctly, no overlaps
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 5. REPAIR (if needed)│  Auto-fixes: shrink font, adjust position, remap
│    per-field fixes    │  If repair fails → flag for human review (hil_flag)
└──────────┬───────────┘
           ▼
      Filled PDF + Report
```

---

## Code Examples

### Python

```python
import requests
import time
import json

API_KEY = "sk_live_YOUR_KEY"
BASE = "https://api.deepread.tech"

# Submit form + data
form_data = {
    "full_name": "Jane Doe",
    "date_of_birth": "03/15/1990",
    "ssn": "123-45-6789",
    "address": "123 Main St, Portland OR 97201"
}

with open("application.pdf", "rb") as f:
    resp = requests.post(
        f"{BASE}/v1/form-fill",
        headers={"X-API-Key": API_KEY},
        files={"file": f},
        data={"form_fields": json.dumps(form_data)}
    )
job_id = resp.json()["id"]

# Poll for results
while True:
    time.sleep(5)
    result = requests.get(
        f"{BASE}/v1/form-fill/{job_id}",
        headers={"X-API-Key": API_KEY}
    ).json()

    if result["status"] in ("completed", "failed"):
        break

if result["status"] == "completed":
    print(f"Download: {result['filled_form_url']}")
    print(f"Fields: {result['fields_filled']}/{result['fields_detected']} filled")
    print(f"Verified: {result['fields_verified']}, Flagged: {result['fields_hil_flagged']}")

    # Check flagged fields
    for field in result["report"]["fields"]:
        if field["hil_flag"]:
            print(f"REVIEW: {field['label']} = {field['value']} ({field.get('reason')})")
else:
    print(f"Failed: {result.get('error_message')}")
```

### JavaScript / Node.js

```javascript
import fs from "fs";

const API_KEY = "sk_live_YOUR_KEY";
const BASE = "https://api.deepread.tech";

// Submit form + data
const form = new FormData();
form.append("file", fs.createReadStream("application.pdf"));
form.append("form_fields", JSON.stringify({
  full_name: "Jane Doe",
  date_of_birth: "03/15/1990",
  ssn: "123-45-6789",
  address: "123 Main St, Portland OR 97201"
}));

const { id: jobId } = await fetch(`${BASE}/v1/form-fill`, {
  method: "POST",
  headers: { "X-API-Key": API_KEY },
  body: form
}).then(r => r.json());

// Poll for results
let result;
do {
  await new Promise(r => setTimeout(r, 5000));
  result = await fetch(`${BASE}/v1/form-fill/${jobId}`, {
    headers: { "X-API-Key": API_KEY }
  }).then(r => r.json());
} while (!["completed", "failed"].includes(result.status));

if (result.status === "completed") {
  console.log("Download:", result.filled_form_url);
  console.log(`Fields: ${result.fields_filled}/${result.fields_detected} filled`);
  console.log(`Verified: ${result.fields_verified}, Flagged: ${result.fields_hil_flagged}`);
} else {
  console.log("Failed:", result.error_message);
}
```

### cURL

```bash
# Submit form + data
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@application.pdf" \
  -F 'form_fields={"full_name": "Jane Doe", "date_of_birth": "03/15/1990", "address": "123 Main St, Portland OR 97201"}'

# Poll for results (use job_id from response)
curl https://api.deepread.tech/v1/form-fill/JOB_ID \
  -H "X-API-Key: YOUR_KEY"

# With webhook and idempotency
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@tax_form.pdf" \
  -F 'form_fields={"taxpayer_name": "Jane Doe", "ssn": "123-45-6789", "filing_status": "Single"}' \
  -F "webhook_url=https://your-app.com/webhooks/form-fill" \
  -F "idempotency_key=submission-abc-123"
```

---

## Idempotency

Prevent duplicate submissions with `idempotency_key`. If you submit the same key twice, the second request returns the existing job instead of creating a new one.

```bash
# First request — creates a new job
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@form.pdf" \
  -F 'form_fields={"name": "Jane"}' \
  -F "idempotency_key=submission-abc-123"
# → {"id": "<job_id>", "status": "queued"}

# Retry with same key — returns the SAME job
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@form.pdf" \
  -F 'form_fields={"name": "Jane"}' \
  -F "idempotency_key=submission-abc-123"
# → {"id": "<same job_id>", "status": "queued"}
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| 400 "Only PDF files are supported" | Upload a `.pdf` file. Other formats are not yet supported. |
| 400 "Invalid JSON in form_fields" | Must be a valid JSON object: `{"name": "Jane"}`, not an array or string. |
| 429 "Monthly page quota exceeded" | Upgrade to Pro or wait until next billing cycle. |
| Status "failed" with "Vision model timeout" | Form is very complex or has many pages. Try splitting into smaller sections. |
| Fields not mapped correctly | Use descriptive JSON keys: `"applicant_full_name"` not `"field1"`. The AI uses key names to match fields. |
| Fields flagged for review | Expected for 2-5% of fields. Check `report.fields` for the `reason` on each flagged field. |

---

## Rate Limits

**Plans:**
| Plan | Pages/month | Price |
|------|-------------|-------|
| Free | 2,000 | $0 (no credit card) |
| Pro | 50,000 | $99/mo |
| Scale | Custom | Custom |

---

## Help the Developer

- **No API key yet** → use `/setup` for the device authorization flow
- **Fill a form** → POST /v1/form-fill, show code in their language
- **Check results** → GET /v1/form-fill/{job_id}, explain the report
- **Flagged fields** → filter by `hil_flag`, explain `reason`, suggest fixes
- **Unmapped keys** → check `unmapped_user_keys`, suggest better key names
- **Real-time updates** → set up `webhook_url`, build receiver endpoint
- **Batch processing** → loop over data, use `idempotency_key` per submission
- **Hitting errors** → check API key, plan limits, file format, JSON validity
