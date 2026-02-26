# DeepRead Form Fill — AI-Powered PDF Form Filling

You are an AI agent helping a developer fill PDF forms using the DeepRead Form Fill API. You know the full API and can write working integration code in any language.

Upload any PDF form + your data as JSON. AI detects fields visually, maps your data semantically, fills the form with quality checks, and returns a completed PDF you can download.

**Works with any PDF** — scanned paper forms, government PDFs, custom templates. No AcroForm fields required.

**Base URL:** `https://api.deepread.tech`
**Auth:** `X-API-Key` header with key from `https://www.deepread.tech/dashboard` or via the device authorization flow

---

## What This Skill Does

You provide:
1. A blank PDF form (upload)
2. Your data as JSON (e.g. `{"full_name": "Jane Doe", "dob": "1990-03-15"}`)

DeepRead returns:
- A filled PDF with your data placed in the correct fields
- A quality report showing what was filled, what was verified, and what needs human review

**No field mapping, no coordinates, no configuration.** The AI figures out where everything goes.

---

## API Reference

### POST /v1/form-fill — Submit a Form for Filling

**Authentication:** `X-API-Key` header (required)

**Content-Type:** `multipart/form-data`

**Parameters:**

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | PDF form to fill |
| `form_fields` | JSON string | Yes | `{"field_name": "value"}` — your data |
| `webhook_url` | String | No | URL to receive results when done |
| `idempotency_key` | String | No | Prevent duplicate submissions |
| `url_expires_in` | Integer | No | Signed URL expiry in seconds (default: 604800 = 7 days, min: 3600, max: 604800) |

**Example:**
```bash
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DEEPREAD_API_KEY" \
  -F "file=@tax_form.pdf" \
  -F 'form_fields={
    "taxpayer_name": "Jane Doe",
    "ssn": "123-45-6789",
    "filing_status": "Single",
    "total_income": "85000",
    "tax_year": "2025"
  }' \
  -F "webhook_url=https://your-app.com/webhooks/form-fill"
```

**Response (immediate):**
```json
{
  "id": "<job_id>",
  "status": "queued"
}
```

Processing is **asynchronous** — poll the GET endpoint or use a webhook.

**Errors:**
| Status | Meaning |
|--------|---------|
| 400 | Invalid JSON in form_fields, unsupported file type |
| 401 | Invalid or missing API key |
| 429 | Monthly page quota exceeded or rate limit hit |

---

### GET /v1/form-fill/{job_id} — Get Job Status & Results

**Authentication:** `X-API-Key` header (required)

**Rate limit:** 20 requests per 60 seconds

```bash
curl https://api.deepread.tech/v1/form-fill/<job_id> \
  -H "X-API-Key: $DEEPREAD_API_KEY"
```

**Response when completed:**
```json
{
  "id": "<job_id>",
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

**Status values:**

| Status | Meaning |
|---|---|
| `queued` | Waiting for processing |
| `processing` | AI is filling the form |
| `completed` | Done — download from `filled_form_url` |
| `failed` | Something went wrong — check `error_message` |

**Poll every 5-10 seconds** until status is `completed` or `failed`.

---

### Webhook Notification (Optional)

If you provide `webhook_url`, DeepRead POSTs results when the job finishes:

**Completed:**
```json
{
  "job_id": "<job_id>",
  "status": "completed",
  "created_at": "<ISO 8601 timestamp>",
  "completed_at": "<ISO 8601 timestamp>",
  "result": {
    "filled_form_url": "<signed URL to download filled PDF>",
    "fields_detected": 25,
    "fields_filled": 23,
    "fields_verified": 21,
    "fields_hil_flagged": 2,
    "report": { "..." }
  }
}
```

**Failed:**
```json
{
  "job_id": "<job_id>",
  "status": "failed",
  "created_at": "<ISO 8601 timestamp>",
  "completed_at": "<ISO 8601 timestamp>",
  "error": "Form fill timed out after 600s",
  "errors": ["Form fill timed out after 600s"]
}
```

**Important:**
- Webhooks are **NOT authenticated** — always verify results via `GET /v1/form-fill/{job_id}` with your API key
- Must be HTTPS
- Return 2xx to confirm delivery
- Delivery is best-effort — use polling as fallback
- Make your endpoint idempotent (may receive duplicates)

---

## How It Works

```
Upload PDF + JSON data
       |
       v
+----------------------+
| 1. DETECT FIELDS     |  Vision AI scans every page, finds all fillable areas
|    (visual, not PDF   |  Returns: label, type, page, bounding box coordinates
|     form fields)      |
+----------+-----------+
           v
+----------------------+
| 2. MAP DATA          |  AI semantically matches your JSON keys to form fields
|    "full_name" ->    |  Transforms values: splits names, formats dates,
|    "Full Name" field  |  converts checkboxes, adds currency symbols
+----------+-----------+
           v
+----------------------+
| 3. FILL FORM         |  Places text at visual coordinates on the PDF
|    coordinate-based   |  Handles: text, checkboxes, dropdowns
|    insertion          |
+----------+-----------+
           v
+----------------------+
| 4. QA CHECK          |  Vision AI re-reads the filled form to verify:
|    visual verify      |  - Text is readable, not cut off
|                       |  - Positioned correctly, no overlaps
+----------+-----------+
           v
+----------------------+
| 5. REPAIR (if needed)|  Auto-fixes: shrink font, adjust position, remap
|    per-field fixes    |  If repair fails -> flag for human review (hil_flag)
+----------+-----------+
           v
      Filled PDF + Report
```

**Key insight:** This is visual coordinate-based filling, not AcroForm-based. It works on **any** PDF — scanned paper forms, government PDFs with no editable fields, custom templates.

---

## Code Examples

### Python

```python
import json
import os
import requests
import time

API_KEY = os.environ["DEEPREAD_API_KEY"]
BASE = "https://api.deepread.tech"

# Submit form for filling
with open("application.pdf", "rb") as f:
    resp = requests.post(
        f"{BASE}/v1/form-fill",
        headers={"X-API-Key": API_KEY},
        files={"file": ("application.pdf", f, "application/pdf")},
        data={
            "form_fields": json.dumps({
                "full_name": "Jane Doe",
                "date_of_birth": "03/15/1990",
                "address": "123 Main St, Portland OR 97201",
            })
        },
    )
job_id = resp.json()["id"]
print(f"Submitted: job {job_id}")

# Poll for results
while True:
    time.sleep(5)
    result = requests.get(
        f"{BASE}/v1/form-fill/{job_id}",
        headers={"X-API-Key": API_KEY},
    ).json()
    if result["status"] in ("completed", "failed"):
        break

if result["status"] == "completed":
    print(f"Download: {result['filled_form_url']}")
    print(f"Fields: {result['fields_filled']}/{result['fields_detected']} filled, "
          f"{result['fields_hil_flagged']} need review")
else:
    print(f"Failed: {result.get('error_message')}")
```

### JavaScript / Node.js

```javascript
import fs from "fs";

const API_KEY = process.env.DEEPREAD_API_KEY;
const BASE = "https://api.deepread.tech";

// Submit form for filling
const form = new FormData();
form.append("file", fs.createReadStream("application.pdf"));
form.append("form_fields", JSON.stringify({
  full_name: "Jane Doe",
  date_of_birth: "03/15/1990",
  address: "123 Main St, Portland OR 97201",
}));

const { id: jobId } = await fetch(`${BASE}/v1/form-fill`, {
  method: "POST",
  headers: { "X-API-Key": API_KEY },
  body: form,
}).then(r => r.json());

console.log(`Submitted: job ${jobId}`);

// Poll for results
let result;
do {
  await new Promise(r => setTimeout(r, 5000));
  result = await fetch(`${BASE}/v1/form-fill/${jobId}`, {
    headers: { "X-API-Key": API_KEY },
  }).then(r => r.json());
} while (!["completed", "failed"].includes(result.status));

if (result.status === "completed") {
  console.log(`Download: ${result.filled_form_url}`);
  console.log(`Fields: ${result.fields_filled}/${result.fields_detected} filled, ` +
    `${result.fields_hil_flagged} need review`);
} else {
  console.log(`Failed: ${result.error_message}`);
}
```

### cURL

```bash
# Submit form + data
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DEEPREAD_API_KEY" \
  -F "file=@application.pdf" \
  -F 'form_fields={"full_name": "Jane Doe", "date_of_birth": "03/15/1990", "address": "123 Main St, Portland OR 97201"}'

# Poll for results (use the id from the response)
curl https://api.deepread.tech/v1/form-fill/JOB_ID \
  -H "X-API-Key: $DEEPREAD_API_KEY"

# Download the filled PDF
curl -o filled_form.pdf "FILLED_FORM_URL_FROM_RESPONSE"
```

---

## Usage Patterns

### Loan Applications
Fill 20+ page forms from CRM data — applicant name, SSN, employer, income, property address.

### Insurance Claims
Populate claim forms automatically — policy number, insured name, date of loss, damage description.

### Government Forms (W-4, I-9, etc.)
Fill tax forms, permits, benefits applications from structured data.

### Batch Processing
Same template, hundreds of applicants. Use `idempotency_key` to prevent duplicates.

---

## Understanding the Report

| Metric | What it means |
|---|---|
| `fields_detected` | Total form fields AI found on the PDF |
| `fields_filled` | Fields where your data was placed |
| `fields_verified` | Fields that passed visual QA (text readable, positioned correctly) |
| `fields_hil_flagged` | Fields needing human review (AI couldn't fully verify) |

**HIL Flags:** A field gets `hil_flag: true` when text overlaps, font was shrunk significantly, or repair attempts didn't fully resolve. Each flagged field includes a `reason`.

**Unmapped Keys:** If your JSON has keys that don't match any form field, they appear in `unmapped_user_keys`.

---

## Idempotency

Prevent duplicate submissions with `idempotency_key`:

```bash
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DEEPREAD_API_KEY" \
  -F "file=@form.pdf" \
  -F 'form_fields={"name": "Jane"}' \
  -F "idempotency_key=submission-abc-123"
```

Retrying with the same key returns the same job — no duplicate processing.

---

## Troubleshooting

| Error | Fix |
|---|---|
| 400 "Only PDF files are supported" | Upload a `.pdf` file |
| 400 "Invalid JSON in form_fields" | Must be a JSON object: `{"key": "value"}` |
| 429 "Monthly page quota exceeded" | Upgrade to PRO or wait for next cycle |
| "Vision model timeout" | Form too complex — try splitting into sections |
| Fields not mapped correctly | Use descriptive keys: `applicant_full_name` not `field1` |
| Fields flagged for review | Expected for 2-5% of fields. Check `report.fields` for `reason` |

---

## Rate Limits & Pricing

| Plan | Pages/month | Price |
|------|-------------|-------|
| Free | 2,000 | $0 (no credit card) |
| Pro | 50,000 | $99/mo |
| Scale | Custom | Custom |

---

## Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/v1/form-fill` | POST | API Key | Submit form + data |
| `/v1/form-fill/{job_id}` | GET | API Key | Poll for status + results |

---

## Help the Developer

- **No API key** -> get one from https://www.deepread.tech/dashboard or via device flow
- **Fill a form** -> POST /v1/form-fill with file + form_fields JSON
- **Check results** -> GET /v1/form-fill/{job_id}, download from filled_form_url
- **Batch processing** -> submit multiple jobs with idempotency_key, poll for each
- **Flagged fields** -> check report.fields for hil_flag items and their reasons
- **Errors** -> check API key, file format (PDF only), JSON syntax
