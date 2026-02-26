---
name: form-fill
description: AI-powered PDF form filling. Upload any PDF form + your data as JSON — AI detects fields, maps your data, fills the form with quality checks, and returns a completed PDF. Works with scanned forms, no AcroForm required.
allowed-tools: Bash, Read, Write
user-invocable: true
---

# DeepRead Form Fill — AI-Powered PDF Form Filling

You are an AI agent helping a developer fill PDF forms using the DeepRead Form Fill API. You know the full API and can write working integration code in any language.

Upload any PDF form + your data as JSON. AI detects fields visually, maps your data semantically, fills the form with quality checks, and returns a completed PDF you can download.

**Works with any PDF** — scanned paper forms, government PDFs, custom templates. No AcroForm fields required.

**Base URL:** `https://api.deepread.tech`
**Auth:** `X-API-Key` header with key from `https://www.deepread.tech/dashboard` or via the `/setup` skill (device authorization flow)

> **No API key?** Use the `/setup` skill first to get one automatically via device flow, or manually set `DEEPREAD_API_KEY` in your `.env` file.

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

## Quick Start

> **IMPORTANT: Split submit and poll into SEPARATE Bash tool calls.**
> Long-running poll loops block the conversation and give the user no way to interact.
> Submit first, confirm the job ID, then poll separately.

### Step 1: Submit the form (one Bash call)

```bash
DR_API_KEY=$(grep ^DEEPREAD_API_KEY .env | cut -d= -f2)

dr_submit=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DR_API_KEY" \
  -F "file=@application.pdf" \
  -F 'form_fields={"full_name": "Jane Doe", "date_of_birth": "03/15/1990", "address": "123 Main St, Portland OR 97201"}')

echo "$dr_submit"
```

Tell the user the job ID and that processing takes 15-30 seconds. Then move on to polling.

### Step 2: Poll for results (separate Bash call)

> **Prefer `run_in_background: true`** for the poll loop so the conversation isn't blocked.

> **Guard against empty job ID.** If `dr_job_id` is empty or "null", stop immediately.

```bash
DR_API_KEY=$(grep ^DEEPREAD_API_KEY .env | cut -d= -f2)
dr_job_id="THE_JOB_ID"

# Guard: bail if job ID is empty
if [ -z "$dr_job_id" ] || [ "$dr_job_id" = "null" ]; then
  echo "ERROR: No job ID — submit may have failed. Check the submit response."
  exit 1
fi

for dr_i in $(seq 1 24); do
  sleep 5
  dr_poll=$(curl -s "https://api.deepread.tech/v1/form-fill/$dr_job_id" -H "X-API-Key: $DR_API_KEY")
  dr_job_status=$(echo "$dr_poll" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))")
  echo "attempt=$dr_i status=$dr_job_status"
  if [ "$dr_job_status" = "completed" ] || [ "$dr_job_status" = "failed" ]; then
    echo "$dr_poll" > /tmp/deepread_formfill_result.json
    python3 -c "
import json
with open('/tmp/deepread_formfill_result.json') as f:
    data = json.load(f)
print(json.dumps({
    'status': data.get('status'),
    'filled_form_url': data.get('filled_form_url'),
    'fields_detected': data.get('fields_detected'),
    'fields_filled': data.get('fields_filled'),
    'fields_verified': data.get('fields_verified'),
    'fields_hil_flagged': data.get('fields_hil_flagged'),
    'duration_seconds': data.get('duration_seconds'),
    'error_message': data.get('error_message'),
}, indent=2))
"
    break
  fi
done
```

### Step 3: Download the filled PDF

The `filled_form_url` in the response is a signed URL. Download it directly:

```bash
curl -o filled_form.pdf "FILLED_FORM_URL_HERE"
```

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

## How It Works (Under the Hood)

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

## Usage Examples

### Loan Application

```bash
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DEEPREAD_API_KEY" \
  -F "file=@loan_application.pdf" \
  -F 'form_fields={
    "applicant_name": "Jane Doe",
    "date_of_birth": "03/15/1990",
    "ssn": "123-45-6789",
    "employer": "Acme Corp",
    "annual_income": "95000",
    "loan_amount": "350000",
    "property_address": "456 Oak Ave, Portland OR 97201",
    "loan_type": "30-Year Fixed"
  }'
```

### Insurance Claim

```bash
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DEEPREAD_API_KEY" \
  -F "file=@claim_form.pdf" \
  -F 'form_fields={
    "policy_number": "INS-2025-78901",
    "insured_name": "Jane Doe",
    "date_of_loss": "06/01/2025",
    "description": "Water damage to basement from pipe burst",
    "estimated_damage": "12500",
    "photos_attached": "true"
  }'
```

### Government Form (W-4, I-9, etc.)

```bash
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DEEPREAD_API_KEY" \
  -F "file=@w4_form.pdf" \
  -F 'form_fields={
    "first_name": "Jane",
    "last_name": "Doe",
    "ssn": "123-45-6789",
    "address": "123 Main St",
    "city": "Portland",
    "state": "OR",
    "zip": "97201",
    "filing_status": "Single",
    "multiple_jobs": "false"
  }'
```

### Batch Processing (Same Template, Different Data)

```python
import json
import os
import requests
import time

API_KEY = os.environ["DEEPREAD_API_KEY"]
FORM_TEMPLATE = "application.pdf"

applicants = [
    {"full_name": "Jane Doe", "email": "jane@example.com", "dob": "1990-03-15"},
    {"full_name": "John Smith", "email": "john@example.com", "dob": "1985-07-22"},
    {"full_name": "Alice Chen", "email": "alice@example.com", "dob": "1992-11-08"},
]

jobs = []
for i, applicant in enumerate(applicants):
    with open(FORM_TEMPLATE, "rb") as f:
        resp = requests.post(
            "https://api.deepread.tech/v1/form-fill",
            headers={"X-API-Key": API_KEY},
            files={"file": (FORM_TEMPLATE, f, "application/pdf")},
            data={
                "form_fields": json.dumps(applicant),
                "idempotency_key": f"batch-2025-06-{i}",
            },
        )
    job_id = resp.json()["id"]
    jobs.append(job_id)
    print(f"Submitted: {applicant['full_name']} -> job {job_id}")

# Poll for results
for job_id in jobs:
    while True:
        result = requests.get(
            f"https://api.deepread.tech/v1/form-fill/{job_id}",
            headers={"X-API-Key": API_KEY},
        ).json()
        if result["status"] in ("completed", "failed"):
            print(f"Job {job_id}: {result['status']}")
            if result["status"] == "completed":
                print(f"  Download: {result['filled_form_url']}")
                print(f"  Fields: {result['fields_filled']}/{result['fields_detected']} filled, "
                      f"{result['fields_hil_flagged']} need review")
            break
        time.sleep(5)
```

---

## Understanding the Report

### fields_detected vs fields_filled vs fields_verified

| Metric | What it means |
|---|---|
| `fields_detected` | Total form fields AI found on the PDF |
| `fields_filled` | Fields where your data was placed |
| `fields_verified` | Fields that passed visual QA (text readable, positioned correctly) |
| `fields_hil_flagged` | Fields needing human review (AI couldn't fully verify) |

**Typical result:** 90-95% of fields verified, 2-5% flagged for review.

### HIL Flags (Human-in-the-Loop)

A field gets `hil_flag: true` when:
- Text overlaps an adjacent field
- Font had to be shrunk significantly
- Value doesn't visually match field expectations
- Repair attempts didn't fully resolve the issue

**Each flagged field includes a `reason`** explaining why review is needed.

### Unmapped Keys

If your JSON has keys that don't match any form field, they appear in `unmapped_user_keys`. This means:
- The form doesn't have a matching field
- Or the field label is ambiguous

---

## Idempotency

Prevent duplicate submissions with `idempotency_key`:

```bash
# First request
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DEEPREAD_API_KEY" \
  -F "file=@form.pdf" \
  -F 'form_fields={"name": "Jane"}' \
  -F "idempotency_key=submission-abc-123"
# -> {"id": "<job_id>", "status": "queued"}

# Retry (same key) — returns the same job, no duplicate
curl -X POST https://api.deepread.tech/v1/form-fill \
  -H "X-API-Key: $DEEPREAD_API_KEY" \
  -F "file=@form.pdf" \
  -F 'form_fields={"name": "Jane"}' \
  -F "idempotency_key=submission-abc-123"
# -> {"id": "<same job_id as above>", "status": "queued"}  <- SAME JOB
```

---

## When to Use Form Fill

### Good For:
- **Loan/mortgage applications** — fill 20+ page forms from CRM data
- **Insurance claims** — populate claim forms automatically
- **Government forms** — W-4, I-9, tax forms, permits, benefits applications
- **Legal documents** — contracts, agreements with field placeholders
- **Onboarding packets** — new hire paperwork from HR systems
- **Batch processing** — same template, hundreds of applicants

### Don't Use For:
- **Creating PDFs from scratch** — this fills existing forms, doesn't generate new ones
- **Real-time (<1 second)** — processing takes 15-30 seconds (async)
- **Non-PDF formats** — PDF only (DOCX support coming soon)

---

## Rate Limits & Pricing

### Free Tier (No Credit Card)
- **2,000 pages/month**
- Full feature access

### Paid Plans
- **PRO**: 50,000 pages/month @ $99/mo
- **SCALE**: Custom volume pricing

**Upgrade:** https://www.deepread.tech/dashboard/billing

---

## Troubleshooting

### Error: 400 "Only PDF files are supported"
Upload a `.pdf` file. Other formats are not yet supported.

### Error: 400 "Invalid JSON in form_fields"
Check your JSON syntax. Must be a valid JSON **object** (not array):
```
OK:  {"name": "Jane Doe", "dob": "1990-03-15"}
BAD: ["name", "dob"]
BAD: "just a string"
```

### Error: 429 "Monthly page quota exceeded"
Upgrade to PRO or wait until next billing cycle.

### Status: "failed" with "Vision model timeout"
The form is very complex or has many pages. Try splitting into smaller sections.

### Fields not mapped correctly
Add more descriptive keys in your JSON. The AI uses your key names to match fields:
```
OK:  {"applicant_full_name": "Jane Doe"}  — clear, matches form labels
BAD: {"field1": "Jane Doe"}  — ambiguous, hard to map
```

### Some fields flagged for review
This is expected for 2-5% of fields. Check `report.fields` for the `reason` on each flagged field.

---

## Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `https://api.deepread.tech/v1/form-fill` | POST | API Key | Submit form + data |
| `https://api.deepread.tech/v1/form-fill/{job_id}` | GET | API Key | Poll for status + results |

---

## Help the Developer

- **No API key yet** -> use `/setup` to get one via device flow, or manually set `DEEPREAD_API_KEY`
- **Fill a form** -> POST /v1/form-fill with file + form_fields JSON
- **Check results** -> GET /v1/form-fill/{job_id}, download from filled_form_url
- **Batch processing** -> submit multiple jobs with idempotency_key, poll for each
- **Flagged fields** -> check report.fields for hil_flag: true items and their reasons
- **Hitting errors** -> check API key, file format (PDF only), JSON syntax
- **Webhook** -> pass webhook_url for push notification instead of polling

---

## Support

- **Dashboard**: https://www.deepread.tech/dashboard
- **Issues**: https://github.com/deepread-tech/deep-read-service/issues
- **Email**: hello@deepread.tech
